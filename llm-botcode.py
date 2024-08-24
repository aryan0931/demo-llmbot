import os
import requests
import zipfile
from github import Github
from transformers import pipeline
import faiss
import numpy as np

# 1. Download and Extract Repo
def download_repo(repo_url, dest_folder):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    
    repo_zip_url = f"{repo_url}/archive/refs/heads/main.zip"
    try:
        repo_zip = requests.get(repo_zip_url)
        repo_zip.raise_for_status()  # Ensure we notice bad responses
        zip_path = os.path.join(dest_folder, "repo.zip")
        with open(zip_path, "wb") as f:
            f.write(repo_zip.content)
        
        # Extract ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(dest_folder)
        os.remove(zip_path)  # Clean up the ZIP file
    except requests.RequestException as e:
        print(f"Error downloading the repo: {e}")
    except zipfile.BadZipFile as e:
        print(f"Error extracting the ZIP file: {e}")

def process_files(folder):
    summaries = []
    for subdir, _, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(subdir, file)
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                    summary = summarize_file(content)
                    summaries.append({"path": file_path, "summary": summary})
                    print(f"Processed file: {file_path}")
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
    return summaries

# 2. GitHub Bot for Capturing Changes
def update_knowledge_base(repo_name, access_token):
    g = Github(access_token)
    repo = g.get_repo(repo_name)
    
    try:
        commits = repo.get_commits()
        latest_commit = commits[0]
        
        summaries = []
        for file in latest_commit.files:
            file_content = repo.get_contents(file.filename, ref=latest_commit.sha).decoded_content.decode()
            summary = summarize_file(file_content)
            summaries.append({"path": file.filename, "summary": summary})
        
        return summaries
    except Exception as e:
        print(f"Error updating knowledge base: {e}")
        return []

# 3. Summarize Files Using LLM
def summarize_file(file_content):
    try:
        summarizer = pipeline("summarization")
        summary = summarizer(file_content, max_length=200, min_length=50, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        print(f"Error summarizing file: {e}")
        return ""

# 4. Vector Database Creation
def create_vector_database(summaries):
    dimension = 768  # Example dimension; this depends on your LLM model
    index = faiss.IndexFlatL2(dimension)
    
    try:
        vectors = np.array([get_vector_from_summary(s['summary']) for s in summaries]).astype('float32')
        index.add(vectors)
    except Exception as e:
        print(f"Error creating vector database: {e}")
    
    return index

def get_vector_from_summary(summary):
    # Placeholder for converting summary to vector using your LLM model
    return np.random.rand(768).astype('float32')

# 5. LLM Agent Node with RAG Database
def run_llm_agent(vector_db, query_vector):
    try:
        D, I = vector_db.search(np.array([query_vector]), k=5)
        return I
    except Exception as e:
        print(f"Error running LLM agent: {e}")
        return []

# 6. GitHub Bot for Issue Handling
def respond_to_issues(repo_name, access_token):
    g = Github(access_token)
    repo = g.get_repo(repo_name)
    
    try:
        issues = repo.get_issues(state="open")
        for issue in issues:
            response = generate_response(issue.body)
            issue.create_comment(response)
    except Exception as e:
        print(f"Error responding to issues: {e}")

def generate_response(issue_body):
    # Placeholder for generating a response using LLM
    return "Automated response based on issue content"

# Example usage
repo_url = "https://github.com/aryan0931/llm-bot"
dest_folder = "local_repo"
access_token = "your_github_access_token"

# Download and process repo
download_repo(repo_url, dest_folder)
summaries = process_files(dest_folder)

# Update knowledge base with latest changes
updated_summaries = update_knowledge_base("user/repo", access_token)

# Create vector database
vector_db = create_vector_database(summaries + updated_summaries)

# Example query vector
query_vector = np.random.rand(768).astype('float32')
print(run_llm_agent(vector_db, query_vector))

# Respond to GitHub issues
respond_to_issues("user/repo", access_token)
