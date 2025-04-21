import os, getpass
env_path = '.env'
from dotenv import load_dotenv
import json
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
load_dotenv(env_path)
from datetime import datetime
from langchain_core.pydantic_v1 import constr, BaseModel, Field, validator
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage,AIMessage
from langchain_core.prompts.chat import ChatPromptTemplate,MessagesPlaceholder
from langchain.pydantic_v1 import BaseModel, Field
from typing_extensions import TypedDict, Annotated
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver
from langchain.tools import StructuredTool
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt import ToolNode
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_community.tools import TavilySearchResults
from langgraph.prebuilt import create_react_agent
from typing import Literal, Optional, List, Dict, Any
from langchain_core.tools import tool
import functools
import pandas as pd
import pymupdf4llm
from docx import Document
import win32com.client


llm = AzureChatOpenAI(temperature=0.7,
                        api_key=os.getenv('AZURE_OPENAI_API_KEY'),
                        azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
                        openai_api_version=os.getenv('AZURE_OPENAI_VERSION'),
                        azure_deployment=os.getenv('AZURE_GPT35_MODEL')
                        )

class LanguageKnown(BaseModel):
    Language: str
    LanguageCode: str

class CountryCode(BaseModel):
    IsoAlpha2: Optional[str] = Field(default=None)
    IsoAlpha3: Optional[str] = Field(default=None)
    UNCode: Optional[str] = Field(default=None)

class ResumeCountry(BaseModel):
    Country: Optional[str] = Field(default=None)
    Evidence: Optional[str] = Field(default=None)
    #CountryCode: CountryCode

class name(BaseModel):
    FullName: Optional[str] = Field(default=None, description="The name of the person")
    TitleName: Optional[str] = Field(default=None)
    FirstName: Optional[str] = Field(default=None)
    MiddleName: Optional[str] = Field(default=None)
    LastName: Optional[str] = Field(default=None)
    FormattedName: Optional[str] = Field(default=None)
    ConfidenceScore: Optional[int] = Field(default=None)

class emailAddress(BaseModel):
    EmailAddress: Optional[str] = Field(default=None, description="The Email of the person")
    ConfidenceScore: Optional[int] = Field(default=None)

class phoneNumber(BaseModel):
    Number: Optional[str] = Field(default=None, description="The mobile number of the person")
    ISDCode: Optional[str] = Field(default=None)
    OriginalNumber: Optional[str] = Field(default=None)
    FormattedNumber: Optional[str] = Field(default=None)
    Type: Optional[str] = Field(default=None)
    ConfidenceScore: Optional[int] = Field(default=None)

class WebSite(BaseModel):
    Type: str
    Url: str

class address(BaseModel):
    Street: Optional[str] = Field(default=None, description="The address of the person")
    City: Optional[str] = Field(default=None)
    State: Optional[str] = Field(default=None)
    StateIsoCode: Optional[str] = Field(default=None)
    Country: Optional[str] = Field(default=None)
    #CountryCode: CountryCode
    ZipCode: Optional[str] = Field(default=None)
    FormattedAddress: Optional[str] = Field(default=None)
    Type: Optional[str] = Field(default=None)
    ConfidenceScore: Optional[int] = Field(default=None)

class Institution(BaseModel):
    Name: Optional[str] = Field(default=None)
    Type: Optional[str] = Field(default=None)
    Location: address
    ConfidenceScore: Optional[int] = Field(default=None)

class Degree(BaseModel):
    DegreeName: Optional[str] = Field(default=None)
    NormalizeDegree: Optional[str] = Field(default=None)
    Specialization: List[str] = Field(default=None)
    ConfidenceScore: Optional[int] = Field(default=None)

class Qualification(BaseModel):
    Institution: Institution
    Degree: Degree
    FormattedDegreePeriod:  Optional[str] = Field(default=None)
    StartDate:  Optional[str] = Field(default=None)
    EndDate:  Optional[str] = Field(default=None)
    Aggregate:  Optional[dict] = Field(default=None)

class Skill(BaseModel):
    Type: Optional[str] = Field(default=None)
    Skill: Optional[str] = Field(default=None)
    Ontology: Optional[str] = Field(default=None)
    Alias: Optional[str] = Field(default=None)
    FormattedName: Optional[str] = Field(default=None)
    Evidence: Optional[str] = Field(default=None)
    LastUsed: Optional[str] = Field(default=None)
    ExperienceInMonths: Optional[int] = Field(default=None)

class Employer(BaseModel):
    EmployerName: Optional[str] = Field(default=None)
    # FormattedName: Optional[str] = Field(default=None)
    # ConfidenceScore: Optional[int] = Field(default=None)

class JobProfile(BaseModel):
    Title: Optional[str] = Field(default=None)
    FormattedName: Optional[str] = Field(default=None)
    Alias: Optional[str] = Field(default=None)
    RelatedSkills: List[dict]
    ConfidenceScore: Optional[int] = Field(default=None)

class Location(BaseModel):
    City: Optional[str] = Field(default=None)
    State: Optional[str] = Field(default=None)
    StateIsoCode: Optional[str] = Field(default=None)
    Country: Optional[str] = Field(default=None)
    #CountryCode: CountryCode

class Experience(BaseModel):
    Employer: Optional[List] = Field(default=None)
    #JobProfile: JobProfile
    #Location: Location
    JobPeriod: Optional[str] = Field(default=None)
    FormattedJobPeriod: Optional[str] = Field(default=None)
    StartDate: Optional[str] = Field(default=None)
    EndDate: Optional[str] = Field(default=None)
    IsCurrentEmployer: Optional[str] = Field(default=None)
    JobDescription: Optional[str] = Field(default=None)
    #Projects: List[dict]

class Person(BaseModel):
    """Information about a person."""

    # ^ Doc-string for the entity Person.
    # This doc-string is sent to the LLM as the description of the schema Person,# and it can help to improve extraction results.

    # Note that:
    # 1. Each field is an `optional` -- this allows the model to decline to extract it!
    # 2. Each field has a `description` -- this description is used by the LLM.
    Name: Optional[str] = Field(default=None, description="The name of the person")
    PhoneNumber: Optional[str] = Field(default=None, description="The mobile number of the person")
    Email: Optional[str] = Field(default=None, description="The Email of the person")
    dob: Optional[str] = Field(default=None, description="The date of birth of the person")
    Address: Optional[str] = Field(default=None, description="The address of the person")
    job_role: Optional[str] = Field(default=None, description="The designation of the person in company")
    skills: List[str] = Field(default=None, description="The skills of the person.list of skills, programming languages, IT tools, software skills")
    years_of_experience: Optional[str] = Field(default=None, description="The years of experience of the person")
    company: Optional[str] = Field(default=None, description="The company of the person")
    education: List[str] = Field(default=None, description=" Extract the education details from the given resume. Include the degree, field of study, institution name, graduation year, and any relevant honors or distinctions. Present the information in a structured format. <degree> <field_of_study> <institution> <graduation_year> <honors>")
    education_institute: Optional[str] = Field(default=None, description="The institute of the education")
    education_year: Optional[str] = Field(default=None, description="The year of education")
    education_degree: Optional[str] = Field(default=None, description="The degree of education")
    course_startdate: Optional[str] = Field(default=None, description="The start date of the course")
    course_enddate: Optional[str] = Field(default=None, description="The end date of the course")
    certification: List[str] = Field(default=None, description="List all the certifications of the person")
    number_of_certifications: Optional[str] = Field(default=None, description="len(certification)")
    awards: List[str] = Field(default=None, description="The awards or achivements of the person")
    refernces: Optional[str] = Field(default=None, description="The refernces of the person")
    miscellaneous: Optional[str] = Field(default=None, description="The mislenious information of the person")
    summary: Optional[str] = Field(default=None, description="summary of person. It should not exceed more than 100 words.")
    Name: name = name()
    Email: emailAddress = emailAddress()
    PhoneNumber: phoneNumber = phoneNumber()
    Address: address = address()
    experience: List[str] = Field(default=None, description= "Extract the following information from the Experience Section of a resume or Curriculum Vitae and breakdown into: <Company name>, <Job role> from <start date> to <end date>")
 
strctured_llm = llm.with_structured_output(schema=Person)

def pdf_to_txt_convertor(file_path_name):
    """
    Converting pdf to Markdown text.
    Text is provided to LLM for exraction
    """
    try:
        md_text = pymupdf4llm.to_markdown(file_path_name)
        return md_text
    except Exception as e:
        print(f'pdf extraction error {file_path_name}:{e}')
        return None
            
def docx_to_txt_convertor(file_path_name):
    """
    Converting doc to text.
    Text is provided to LLM for exraction
    """
    try:
        doc = Document(file_path_name)
        full_txt = []
        for paragraph in doc.paragraphs:
            full_txt.append(paragraph.text)
        return '\n'.join(full_txt)
    except Exception as e:
        print(f'Docx Conversion Error:{file_path_name}:{e}')
        return None

def extract_txt_from_resume(file_path_name):
    try:
        if file_path_name.endswith('.pdf'):
            return pdf_to_txt_convertor(file_path_name)
        elif file_path_name.endswith('.docx'):
            return docx_to_txt_convertor(file_path_name)
        else:
            print(f'unsuported file format: {file_path_name}')
            return None
    except Exception as e:
        print(f'Resume text extraction error:{e}')
        return None

prompt_template = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are specialized agent to provide extracted information from resume."
        "If the value is not known fillvalue with null."
        "Do not make or create or generate any information which is not provided"
    ),
    (
        "human","{text}"
    )
])

prompt = prompt_template.invoke({"text":extract_txt_from_resume("john doe.pdf")})
llm_response = strctured_llm.invoke(prompt)
response_dict = llm_response.dict()
response_json = json.dumps(response_dict,indent = 4)
print(response_json)

                       
