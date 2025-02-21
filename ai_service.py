from openai import OpenAI
from config import DEEPSEEK_API_KEY, OPENAI_API_KEY
from enum import Enum

class AIModel(Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"

class AIService:
    def __init__(self, model_type: AIModel):
        self.model_type = model_type
        if model_type == AIModel.DEEPSEEK:
            self.client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com"
            )
        else:  # OpenAI
            self.client = OpenAI(api_key=OPENAI_API_KEY)

    def create_completion(self, messages):
        try:
            if self.model_type == AIModel.DEEPSEEK:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    temperature=0.7,  # Add some creativity but not too much
                    max_tokens=2000,  # Ensure enough tokens for response
                    stream=False
                )
            else:  # OpenAI
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000
                )
            
            print("Raw AI Response:", response)  # Debug print
            return True, response.choices[0].message.content
            
        except Exception as e:
            print(f"API Error: {str(e)}")  # Debug print
            return False, str(e)

    def optimize_resume(self, jobs):
        system_prompt = """You are a resume optimization expert. Your task is to analyze the jobs and their bullet points, 
        then return a JSON object with optimized ordering. Format your response exactly like this:
        {
            "job_order": {
                "1": 1,  // job_id: order_number (1 is highest priority)
                "2": 2
            },
            "point_orders": {
                "1": {  // job_id
                    "1": {"order": 1, "score": 0.95},  // point_id: {order, relevance_score}
                    "2": {"order": 2, "score": 0.85}
                }
            }
        }
        Order jobs by relevance and impact, and order bullet points to highlight the most impressive achievements first."""
        
        jobs_data = {
            "jobs": [{
                "id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "points": [{"id": point_id, "text": point} 
                          for point_id, point in zip(job["point_ids"], job["points"])]
            } for job in jobs]
        }
        
        try:
            print("Sending to AI:", jobs_data)  # Debug print
            
            success, response = self.create_completion([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please optimize this resume data and return in the specified JSON format: {str(jobs_data)}"}
            ])
            
            print("AI Response:", response)  # Debug print
            
            if success:
                parsed = self._parse_optimization_response(response)
                print("Parsed Response:", parsed)  # Debug print
                
                # Validate the parsed response
                if not parsed["job_order"] or not parsed["point_orders"]:
                    return False, "AI response missing required data"
                    
                return True, parsed
                
            return False, "Failed to get AI response"
            
        except Exception as e:
            print(f"Optimization error: {str(e)}")  # Debug print
            return False, str(e)
    
    def _parse_optimization_response(self, response):
        try:
            import json
            import re
            
            # Extract JSON object from the response using regex
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                return {"job_order": {}, "point_orders": {}}
            
            json_str = json_match.group(0)
            print("Extracted JSON:", json_str)  # Debug print
            
            # Parse the JSON
            parsed = json.loads(json_str)
            
            # Convert string keys to integers
            job_order = {int(k): int(v) for k, v in parsed["job_order"].items()}
            
            point_orders = {}
            for job_id, points in parsed["point_orders"].items():
                job_id = int(job_id)
                point_orders[job_id] = {
                    str(point_id): {  # Keep point_id as string since that's how we store it
                        "order": int(data["order"]),
                        "score": float(data["score"])
                    }
                    for point_id, data in points.items()
                }
            
            return {
                "job_order": job_order,
                "point_orders": point_orders
            }
            
        except Exception as e:
            print(f"Error parsing AI response: {str(e)}")
            return {"job_order": {}, "point_orders": {}}

def test_ai_connection(model_type: AIModel):
    ai_service = AIService(model_type)
    return ai_service.create_completion([
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Test connection"}
    ])