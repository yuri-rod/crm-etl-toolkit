#!/usr/bin/env python3
"""
Script to deploy a text model to a Vertex AI endpoint using Publisher Models.
"""

import os
import sys
import time
import json
import traceback
import importlib
import pkg_resources
from google.cloud import aiplatform
from google.api_core import exceptions as google_exceptions

# For compatibility with different versions of the SDK
try:
    from vertexai.language_models import TextGenerationModel
    from vertexai.generative_models import GenerativeModel
    VERTEXAI_AVAILABLE = True
    print("Using vertexai package for language models")
except ImportError:
    try:
        from google.cloud.aiplatform.preview.language_models import TextGenerationModel
        VERTEXAI_AVAILABLE = True
        print("Using google.cloud.aiplatform.preview for language models")
    except ImportError:
        VERTEXAI_AVAILABLE = False
        print("Warning: Advanced language model features not available in this SDK version")

# Initialize Vertex AI with project and region
PROJECT_ID = "crm-data-461221"
REGION = "us-central1"  # Using us-central1 where most foundation models are available
ENDPOINT_ID = "3269135041912897536"  # New endpoint ID in us-central1

# Model information - focusing on Gemini Pro as primary model
MODEL_DISPLAY_NAME = "gemini-deployment"
GEMINI_MODEL = "gemini-pro"  # Use Gemini Pro as primary model
FOUNDATION_MODEL = "text-bison"  # Fallback model
MODEL_VERSION = "@001"  # Version for text-bison if used
PUBLISHER = "google"

# Error handling constants
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Get SDK version for diagnostics
def get_sdk_version():
    """Get the version of the installed Vertex AI SDK."""
    try:
        return pkg_resources.get_distribution("google-cloud-aiplatform").version
    except:
        return "Unknown"

SDK_VERSION = get_sdk_version()
print(f"Using Google Cloud AI Platform SDK version: {SDK_VERSION}")

# Initialize the Vertex AI SDK
aiplatform.init(project=PROJECT_ID, location=REGION)

def verify_credentials():
    """Verify that credentials are properly set up."""
    try:
        print("Verifying credentials...")
        # List endpoints to verify credentials work
        endpoints = aiplatform.Endpoint.list(project=PROJECT_ID, location=REGION)
        print(f"✓ Credentials verified. Found {len(endpoints)} endpoints.")
        return True
    except google_exceptions.GoogleAPIError as e:
        print(f"❌ Credential verification failed: {e}")
        print("Please run 'gcloud auth application-default login' to set up credentials.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during credential verification: {e}")
        return False

def use_vertexai_prediction():
    """Use Vertex AI's specialized language model APIs for prediction."""
    if not VERTEXAI_AVAILABLE:
        print("\n❌ Vertex AI language model modules not available.")
        print("Please install the vertexai package with: pip install google-cloud-aiplatform[vertexai]")
        return False
    
    print("\nSetting up prediction using Vertex AI language models...")
    
    try:
        # First, properly initialize vertexai if needed
        try:
            import vertexai
            vertexai.init(project=PROJECT_ID, location=REGION)
            print("Initialized vertexai package")
        except (ImportError, AttributeError):
            print("Using google.cloud.aiplatform directly")
        
        # Initialize the TextGenerationModel
        print(f"Loading model: {FOUNDATION_MODEL}{MODEL_VERSION}")
        model = TextGenerationModel.from_pretrained(FOUNDATION_MODEL + MODEL_VERSION)
        print(f"✓ Successfully initialized model: {FOUNDATION_MODEL}{MODEL_VERSION}")
        
        # Test with a prediction
        prompt = "Explain what an MCP server is in Vertex AI."
        print(f"\nSending test prompt: '{prompt}'")
        
        parameters = {
            "temperature": 0.2,
            "max_output_tokens": 1024,
            "top_p": 0.8,
            "top_k": 40
        }
        
        # Handle different API versions
        try:
            # Newer API style
            response = model.predict(prompt=prompt, **parameters)
            result_text = response.text
        except TypeError:
            # Older API style
            response = model.predict(prompt, **parameters)
            result_text = response
        
        print("\n✓ Prediction successful!")
        print("\nResponse:")
        print(result_text)
        
        return True
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        print("\nDetailed traceback:")
        traceback.print_exc()
        return False

def deploy_model_to_endpoint():
    """Deploy a model to the endpoint."""
    print(f"\nDeploying model to endpoint {ENDPOINT_ID}...")
    
    try:
        # Get the endpoint
        endpoint = aiplatform.Endpoint(endpoint_name=ENDPOINT_ID)
        print(f"✓ Successfully retrieved endpoint: {endpoint.display_name}")
        
        # Create a deployment on the endpoint
        deployed_model = endpoint.deploy(
            model=GEMINI_MODEL,  # Use Gemini model name directly
            deployed_model_display_name=MODEL_DISPLAY_NAME,
            machine_type="n1-standard-4",
            min_replica_count=1,
            max_replica_count=1,
            traffic_percentage=100
        )
        
        print(f"✓ Successfully deployed {GEMINI_MODEL} to endpoint {ENDPOINT_ID}")
        return True
    except google_exceptions.PermissionDenied as e:
        print(f"❌ Permission denied when deploying model: {e}")
        print("Please ensure you have the necessary permissions to deploy models.")
        return False
    except google_exceptions.InvalidArgument as e:
        print(f"❌ Invalid argument when deploying model: {e}")
        print("The model name or parameters may be incorrect.")
        return False
    except Exception as e:
        print(f"❌ Model deployment failed: {e}")
        print("\nDetailed traceback:")
        traceback.print_exc()
        return False

def use_rest_api_prediction():
    """Use REST API for prediction when SDK methods aren't available."""
    print("\nAttempting prediction using REST API...")
    
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            # Use the Prediction API client
            client_options = {"api_endpoint": f"{REGION}-aiplatform.googleapis.com"}
            prediction_client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)
            
            # Format the endpoint path
            endpoint_path = f"projects/{PROJECT_ID}/locations/{REGION}/endpoints/{ENDPOINT_ID}"
            print(f"Using endpoint: {endpoint_path}")
            
            # Create the prediction request for Gemini
            instance = {
                "contents": [{
                    "role": "user",
                    "parts": [{
                        "text": "Explain what an MCP server is in Vertex AI."
                    }]
                }]
            }
            instances = [instance]
            
            parameters = {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
                "topP": 0.8,
                "topK": 40
            }
            
            # Make the prediction request
            response = prediction_client.predict(
                endpoint=endpoint_path,
                instances=instances,
                parameters=parameters
            )
            
            print("\n✓ REST API prediction successful!")
            print("\nResponse:")
            print(response)
            
            return True
        except google_exceptions.PermissionDenied as e:
            print(f"❌ Permission denied: {e}")
            print("Please ensure you have the necessary permissions to use this endpoint.")
            return False
        except google_exceptions.ResourceExhausted as e:
            print(f"❌ API quota exceeded: {e}")
            print("You may have exceeded your API quota limits.")
            return False
        except google_exceptions.NotFound as e:
            print(f"❌ Resource not found: {e}")
            print(f"Please verify that endpoint ID {ENDPOINT_ID} exists in project {PROJECT_ID}.")
            return False
        except Exception as e:
            print(f"❌ REST API prediction failed: {e}")
            print("\nDetailed traceback:")
            traceback.print_exc()
            
            retry_count += 1
            if retry_count < MAX_RETRIES:
                print(f"Retrying ({retry_count}/{MAX_RETRIES})...")
                time.sleep(RETRY_DELAY)
            else:
                return False
    
    return False

def use_gemini_model():
    """Try using Gemini model if available."""
    print("\nAttempting to use Gemini model...")
    
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            # Initialize vertexai
            import vertexai
            vertexai.init(project=PROJECT_ID, location=REGION)
            
            # Create the model
            model = GenerativeModel(GEMINI_MODEL)
            print(f"✓ Successfully loaded {GEMINI_MODEL} model")
            
            # Set safety settings to allow more content through
            safety_settings = {
                "HARASCRMNT": "BLOCK_NONE",
                "HATE_SPEECH": "BLOCK_NONE",
                "SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "DANGEROUS_CONTENT": "BLOCK_NONE"
            }
            
            # Generate content with a system instruction
            prompt = "Explain what an MCP server is in Vertex AI. Include details about Model Container Platform and how it's used for model deployment."
            
            # Set up generation config
            generation_config = {
                "temperature": 0.2,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
            
            print(f"\nSending test prompt to {GEMINI_MODEL}: '{prompt}'")
            
            # Try with safety settings
            try:
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
            except:
                # If safety settings fail, try without them
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
            
            print("\n✓ Gemini model prediction successful!")
            print("\nResponse:")
            print(response.text)
            
            return True
        except google_exceptions.PermissionDenied as e:
            print(f"❌ Permission denied: {e}")
            print("Please ensure Gemini API is enabled for your project.")
            return False
        except google_exceptions.ResourceExhausted as e:
            print(f"❌ Resource exhausted (quota exceeded): {e}")
            print("You may have exceeded your API quota. Check your Google Cloud console.")
            return False
        except google_exceptions.NotFound as e:
            error_message = str(e)
            if "not found or your project does not have access to it" in error_message:
                print(f"❌ Model not found: {e}")
                print(f"Please ensure {GEMINI_MODEL} is available in your region and project.")
                return False
            else:
                print(f"❌ Resource not found: {e}")
                retry_count += 1
                if retry_count < MAX_RETRIES:
                    print(f"Retrying ({retry_count}/{MAX_RETRIES})...")
                    time.sleep(RETRY_DELAY)
                continue
        except Exception as e:
            print(f"❌ Gemini model prediction failed: {e}")
            print("\nDetailed traceback:")
            traceback.print_exc()
            
            retry_count += 1
            if retry_count < MAX_RETRIES:
                print(f"Retrying ({retry_count}/{MAX_RETRIES})...")
                time.sleep(RETRY_DELAY)
            else:
                return False
    
    return False

def run_sdk_version_diagnostics():
    """Run diagnostics to check SDK compatibility."""
    print("\nRunning SDK version diagnostics...")
    
    # Check for required packages
    packages = [
        "google-cloud-aiplatform",
        "vertexai"
    ]
    
    for package in packages:
        try:
            version = pkg_resources.get_distribution(package).version
            print(f"✓ {package} version {version} installed")
        except pkg_resources.DistributionNotFound:
            print(f"❌ {package} not installed")
    
    # Check for available modules
    modules = [
        ("google.cloud.aiplatform", "Base Vertex AI SDK"),
        ("vertexai", "Vertex AI Python SDK"),
        ("vertexai.language_models", "Vertex AI Language Models"),
        ("vertexai.generative_models", "Vertex AI Generative Models"),
        ("google.cloud.aiplatform.preview", "Vertex AI Preview Features")
    ]
    
    for module_name, description in modules:
        try:
            module = importlib.import_module(module_name)
            print(f"✓ {description} ({module_name}) available")
        except ImportError:
            print(f"❌ {description} ({module_name}) not available")
    
    print("\nRecommended action:")
    print("If language models are not available, install the full Vertex AI package:")
    print("pip install google-cloud-aiplatform[vertexai]")
    
    return True

def check_api_access():
    """Check if all required APIs are enabled."""
    print("\nChecking API access...")
    
    required_apis = [
        "aiplatform.googleapis.com",
        "artifactregistry.googleapis.com"
    ]
    
    try:
        # Simple check - if we can list models, the API is enabled
        endpoints = aiplatform.Endpoint.list(project=PROJECT_ID, location=REGION)
        print(f"✓ Vertex AI API is enabled. Found {len(endpoints)} endpoints.")
        return True
    except google_exceptions.PermissionDenied as e:
        print(f"❌ Permission denied: {e}")
        print("Please ensure the following APIs are enabled:")
        for api in required_apis:
            print(f"  - {api}")
        print("\nRun the following command to enable them:")
        print(f"gcloud services enable {' '.join(required_apis)}")
        return False
    except Exception as e:
        print(f"❌ Error checking API access: {e}")
        return False

def main():
    """Main function to run the script."""
    print("Vertex AI Model Deployment Script")
    print("=================================")
    print(f"Project: {PROJECT_ID}")
    print(f"Region: {REGION}")
    print(f"Endpoint ID: {ENDPOINT_ID}")
    print(f"Primary Model: {GEMINI_MODEL}")
    print(f"SDK Version: {SDK_VERSION}")
    print("=================================")
    
    try:
        # First verify credentials
        if not verify_credentials():
            print("\n❌ Credential verification failed. Please authenticate first.")
            print("Run: gcloud auth application-default login")
            sys.exit(1)
        
        # Check API access
        if not check_api_access():
            print("\n❌ API access check failed. Please enable required APIs.")
            sys.exit(1)
        
        # Try Gemini as the primary approach
        print("\nAttempting to use Gemini model...")
        success = use_gemini_model()
        
        if success:
            print("\n✓ Successfully used Gemini model.")
            print("\nNote: For production use, you can either:")
            print("  1. Continue using direct prediction (simplest approach)")
            print("  2. Use Vertex AI Tuning to customize the model")
            print("  3. Deploy a model to an endpoint (advanced)")
            
            # Optionally try deploying to endpoint
            deploy_model = input("\nWould you like to deploy the model to the endpoint? (y/n): ").lower()
            if deploy_model == 'y':
                deploy_success = deploy_model_to_endpoint()
                if deploy_success:
                    print("\n✓ Model successfully deployed to endpoint.")
                else:
                    print("\n❌ Model deployment to endpoint failed.")
        else:
            # Try text-bison as a fallback
            print("\nAttempting to use text-bison as a fallback...")
            success = use_vertexai_prediction()
            
            if success:
                print("\n✓ Successfully used text-bison model.")
            else:
                # Try REST API as a last resort
                print("\nAttempting to use REST API for prediction...")
                success = use_rest_api_prediction()
                
                if success:
                    print("\n✓ Successfully used REST API for prediction.")
                else:
                    # Run diagnostics for troubleshooting
                    run_sdk_version_diagnostics()
                    
                    print("\n❌ All approaches failed.")
                    print("\nTroubleshooting suggestions:")
                    print("1. Ensure you have enabled the Vertex AI API")
                    print("2. Check if Gemini API is enabled for your project")
                    print("3. Verify your project has permission to use these models")
                    print("4. Check if you have exceeded your API quota limits")
                    print("5. Make sure you have the latest SDK versions installed")
                    print("\nRun this command to enable needed APIs:")
                    print("gcloud services enable aiplatform.googleapis.com artifactregistry.googleapis.com")
                    
                    sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        traceback.print_exc()
        # Run diagnostics for troubleshooting
        run_sdk_version_diagnostics()
        sys.exit(1)

if __name__ == "__main__":
    main()

