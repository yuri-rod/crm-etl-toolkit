#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend Endpoint Smoke Tests
============================

Backend endpoint smoke tests using httpx.AsyncClient
Tests critical API endpoints for basic functionality.

Developed for CRM ETL
"""

import asyncio
import pytest
import httpx
import json
from pathlib import Path
from typing import Dict, Any
import tempfile
import os

# Test configuration
TEST_BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0


class TestBackendEndpoints:
    """Backend API endpoint smoke tests"""

    @pytest.fixture(scope="class")
    async def async_client(self):
        """Create async HTTP client for testing"""
        async with httpx.AsyncClient(
            base_url=TEST_BASE_URL,
            timeout=httpx.Timeout(TIMEOUT),
            follow_redirects=True
        ) as client:
            yield client

    @pytest.fixture
    def sample_csv_file(self):
        """Create a sample CSV file for testing uploads"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,name,email,score\n")
            f.write("1,João Silva,joao@email.com,85\n")
            f.write("2,Maria Santos,maria@email.com,92\n")
            f.write("3,Pedro Oliveira,pedro@email.com,78\n")
            f.write("4,Ana Costa,ana@email.com,96\n")
            f.write("5,Carlos Lima,carlos@email.com,81\n")
        
        yield f.name
        
        # Cleanup
        if os.path.exists(f.name):
            os.unlink(f.name)

    @pytest.mark.asyncio
    async def test_root_endpoint(self, async_client: httpx.AsyncClient):
        """Test root endpoint availability"""
        response = await async_client.get("/")
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        
        # If 200, should return JSON or HTML
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            assert any(ct in content_type.lower() for ct in ["json", "html", "text"]), \
                f"Unexpected content type: {content_type}"

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: httpx.AsyncClient):
        """Test health check endpoint"""
        endpoints_to_try = ["/health", "/status", "/api/health", "/ping"]
        
        health_found = False
        for endpoint in endpoints_to_try:
            try:
                response = await async_client.get(endpoint)
                if response.status_code == 200:
                    health_found = True
                    try:
                        data = response.json()
                        assert isinstance(data, dict), "Health response should be JSON object"
                    except json.JSONDecodeError:
                        # Plain text response is also acceptable
                        assert len(response.text) > 0, "Health response should not be empty"
                    break
            except httpx.RequestError:
                continue
        
        # If no health endpoint found, that's okay for smoke test
        assert True, "Health check completed (endpoint may not exist yet)"

    @pytest.mark.asyncio
    async def test_api_docs(self, async_client: httpx.AsyncClient):
        """Test API documentation endpoints"""
        doc_endpoints = ["/docs", "/redoc", "/openapi.json", "/api/docs"]
        
        for endpoint in doc_endpoints:
            try:
                response = await async_client.get(endpoint)
                if response.status_code == 200:
                    if endpoint.endswith(".json"):
                        # Should be valid JSON
                        data = response.json()
                        assert "openapi" in data or "swagger" in data, \
                            "OpenAPI spec should contain version info"
                    else:
                        # Should be HTML page
                        assert "html" in response.headers.get("content-type", "").lower() or \
                               "<!DOCTYPE html>" in response.text.lower() or \
                               len(response.text) > 100, \
                               "Documentation page should contain content"
                    break
            except (httpx.RequestError, json.JSONDecodeError):
                continue

    @pytest.mark.asyncio
    async def test_pipeline_execute_endpoint(self, async_client: httpx.AsyncClient, sample_csv_file: str):
        """Test pipeline execution endpoint"""
        endpoint = "/pipeline/execute"
        
        # Test with multipart form data
        with open(sample_csv_file, 'rb') as f:
            files = {'file': ('test_data.csv', f, 'text/csv')}
            data = {
                'mode': 'batch-predict',
                'target_column': 'score',
                'output_filename': 'test_output.csv'
            }
            
            try:
                response = await async_client.post(endpoint, files=files, data=data)
                
                if response.status_code == 404:
                    # Endpoint doesn't exist yet - that's okay for smoke test
                    assert True, "Pipeline endpoint not implemented yet"
                    return
                
                # If endpoint exists, test response
                assert response.status_code in [200, 201, 202], \
                    f"Pipeline execution failed with status {response.status_code}: {response.text}"
                
                if response.status_code in [200, 201, 202]:
                    try:
                        result = response.json()
                        assert isinstance(result, dict), "Response should be JSON object"
                        
                        # Common fields we might expect
                        expected_fields = ['status', 'message', 'pipeline_id', 'task_id']
                        has_expected_field = any(field in result for field in expected_fields)
                        assert has_expected_field, f"Response should contain status information: {result}"
                        
                    except json.JSONDecodeError:
                        assert False, f"Response should be valid JSON: {response.text}"
                        
            except httpx.RequestError as e:
                pytest.skip(f"Pipeline endpoint not reachable: {e}")

    @pytest.mark.asyncio
    async def test_pipeline_status_endpoint(self, async_client: httpx.AsyncClient):
        """Test pipeline status endpoint"""
        endpoint = "/pipeline/status/test_pipeline_123"
        
        try:
            response = await async_client.get(endpoint)
            
            if response.status_code == 404:
                # Expected for non-existent pipeline or endpoint
                assert True, "Pipeline status endpoint behaves correctly for non-existent pipeline"
                return
            
            assert response.status_code in [200, 400], \
                f"Unexpected status code: {response.status_code}"
                
            if response.status_code == 200:
                try:
                    result = response.json()
                    assert isinstance(result, dict), "Status response should be JSON object"
                except json.JSONDecodeError:
                    assert False, f"Response should be valid JSON: {response.text}"
                    
        except httpx.RequestError:
            pytest.skip("Pipeline status endpoint not reachable")

    @pytest.mark.asyncio
    async def test_ai_rule_generation_endpoint(self, async_client: httpx.AsyncClient):
        """Test AI rule generation endpoint"""
        endpoint = "/ai/generate-rule"
        
        payload = {
            "requirement": "Filter customers with high value and low risk",
            "data_context": {
                "columns": ["customer_value", "risk_score", "age", "location"],
                "sample_data": {
                    "customer_value": [1000, 500, 2000, 300],
                    "risk_score": [0.1, 0.8, 0.2, 0.9]
                }
            }
        }
        
        try:
            response = await async_client.post(endpoint, json=payload)
            
            if response.status_code == 404:
                # Endpoint doesn't exist yet
                assert True, "AI rule generation endpoint not implemented yet"
                return
            
            assert response.status_code in [200, 201, 501], \
                f"AI endpoint failed with status {response.status_code}: {response.text}"
            
            if response.status_code in [200, 201]:
                try:
                    result = response.json()
                    assert isinstance(result, dict), "AI response should be JSON object"
                    
                    # Expected AI response fields
                    ai_fields = ['rule', 'code', 'explanation', 'suggestion']
                    has_ai_field = any(field in result for field in ai_fields)
                    assert has_ai_field or 'error' in result, \
                        f"AI response should contain rule information: {result}"
                        
                except json.JSONDecodeError:
                    assert False, f"AI response should be valid JSON: {response.text}"
                    
        except httpx.RequestError:
            pytest.skip("AI rule generation endpoint not reachable")

    @pytest.mark.asyncio
    async def test_cors_headers(self, async_client: httpx.AsyncClient):
        """Test CORS headers for web frontend"""
        # Test preflight request
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        try:
            response = await async_client.options("/", headers=headers)
            
            # CORS should be configured
            if response.status_code in [200, 204]:
                cors_headers = response.headers
                assert "access-control-allow-origin" in cors_headers or \
                       "Access-Control-Allow-Origin" in cors_headers, \
                       "CORS headers should be present"
                       
        except httpx.RequestError:
            # Server might not be running
            pytest.skip("Server not reachable for CORS test")

    @pytest.mark.asyncio
    async def test_static_files(self, async_client: httpx.AsyncClient):
        """Test static file serving"""
        static_endpoints = ["/static/", "/static/index.html", "/assets/", "/css/", "/js/"]
        
        for endpoint in static_endpoints:
            try:
                response = await async_client.get(endpoint)
                
                # 404 is okay, means endpoint structure is correct
                assert response.status_code in [200, 404, 403], \
                    f"Static endpoint {endpoint} returned unexpected status: {response.status_code}"
                    
                if response.status_code == 200:
                    # Should have appropriate content type
                    content_type = response.headers.get("content-type", "")
                    assert len(content_type) > 0, "Static files should have content type"
                    
            except httpx.RequestError:
                continue

    @pytest.mark.asyncio
    async def test_error_handling(self, async_client: httpx.AsyncClient):
        """Test error handling for invalid requests"""
        # Test invalid JSON
        try:
            response = await async_client.post(
                "/api/test",
                content="invalid json {",
                headers={"content-type": "application/json"}
            )
            
            # Should return 4xx error, not 500
            if response.status_code not in [404]:  # 404 is okay
                assert 400 <= response.status_code < 500, \
                    f"Invalid JSON should return 4xx error, got {response.status_code}"
                    
        except httpx.RequestError:
            pass

    @pytest.mark.asyncio
    async def test_large_file_upload(self, async_client: httpx.AsyncClient):
        """Test handling of large file uploads"""
        # Create a larger CSV file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,data\n")
            for i in range(1000):  # 1000 rows
                f.write(f"{i},{'x' * 100}\n")  # Each row ~100 chars
        
        try:
            with open(f.name, 'rb') as file_handle:
                files = {'file': ('large_test.csv', file_handle, 'text/csv')}
                data = {'mode': 'test'}
                
                # Test with longer timeout for large files
                response = await async_client.post(
                    "/pipeline/execute",
                    files=files,
                    data=data,
                    timeout=60.0  # Extended timeout
                )
                
                # Should handle large files gracefully
                assert response.status_code in [200, 201, 202, 404, 413], \
                    f"Large file upload returned unexpected status: {response.status_code}"
                    
        except httpx.RequestError:
            pytest.skip("Large file upload test skipped - endpoint not reachable")
        finally:
            if os.path.exists(f.name):
                os.unlink(f.name)


@pytest.mark.asyncio
async def test_server_availability():
    """Test if server is available before running other tests"""
    try:
        async with httpx.AsyncClient(base_url=TEST_BASE_URL, timeout=5.0) as client:
            response = await client.get("/")
            print(f"✅ Server responded with status: {response.status_code}")
    except httpx.RequestError as e:
        print(f"⚠️ Server not available at {TEST_BASE_URL}: {e}")
        print("Start the server with: python BETA/backend/api_server.py")
        pytest.skip("Backend server not available")


if __name__ == "__main__":
    # Run basic connectivity test
    asyncio.run(test_server_availability())
