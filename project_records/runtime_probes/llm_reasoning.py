import os
import vertexai
from vertexai.generative_models import GenerativeModel

# Optionally set inside Python instead of env var
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = __import__('os').environ['GOOGLE_APPLICATION_CREDENTIALS']

# Initialize Vertex AI
vertexai.init(project=__import__('os').environ['GOOGLE_CLOUD_PROJECT'], location="us-central1")

# Use Gemini model
model = GenerativeModel("gemini-2.5-flash")
resp = model.generate_content("Write a haiku about Athens sunset")
print(resp.text)