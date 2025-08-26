import os
import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from playwright.sync_api import sync_playwright, Page, Browser

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmailService(Enum):
    GMAIL = "gmail"
    OUTLOOK = "outlook"

@dataclass
class EmailInstruction:
    recipient: str
    subject: str
    body: str
    service: EmailService

class LLMClient:
    """Mock LLM client for instruction parsing and UI analysis"""
    
    def parse_email_instruction(self, instruction: str) -> EmailInstruction:
        """Parse natural language instruction into structured email data"""
        # In a real implementation, this would call an actual LLM API
        # For this exercise, we'll use simple pattern matching
        
        logger.info(f"Parsing instruction: {instruction}")
        
        # Simple parsing logic - in reality, this would use proper NLP
        recipient = "test@example.com"  # Default
        subject = "Automated Email"
        body = "This is an automated email sent by the Humaein AI agent."
        service = EmailService.GMAIL
        
        # Extract recipient if mentioned
        if "to " in instruction.lower():
            parts = instruction.lower().split("to ")
            if len(parts) > 1:
                recipient_part = parts[1].split(" ")[0]
                if "@" in recipient_part:
                    recipient = recipient_part
        
        # Extract subject if mentioned
        if "about " in instruction.lower():
            parts = instruction.lower().split("about ")
            if len(parts) > 1:
                subject = parts[1].split(".")[0].capitalize()
        
        # Extract service preference if mentioned
        if "gmail" in instruction.lower():
            service = EmailService.GMAIL
        elif "outlook" in instruction.lower():
            service = EmailService.OUTLOOK
        
        return EmailInstruction(recipient, subject, body, service)
    
    def analyze_ui_and_generate_actions(self, html: str, goal: str) -> List[Dict]:
        """Analyze UI and generate action sequence"""
        # In a real implementation, this would call an actual LLM API
        # For this exercise, we'll return predefined actions based on the goal
        
        logger.info(f"Analyzing UI for goal: {goal}")
        
        if "gmail" in goal.lower():
            return [
                {"action": "click", "selector": "div[role='button'][gh='cm']", "description": "Click compose button"},
                {"action": "fill", "selector": "input[aria-label='To']", "value": "${recipient}", "description": "Fill recipient field"},
                {"action": "fill", "selector": "input[aria-label='Subject']", "value": "${subject}", "description": "Fill subject field"},
                {"action": "fill", "selector": "div[aria-label='Message Body']", "value": "${body}", "description": "Fill body field"},
                {"action": "click", "selector": "div[role='button'][aria-label*='Send']", "description": "Click send button"}
            ]
        else:  # outlook
            return [
                {"action": "click", "selector": "button[aria-label='New message']", "description": "Click new message button"},
                {"action": "fill", "selector": "input[aria-label='To']", "value": "${recipient}", "description": "Fill recipient field"},
                {"action": "fill", "selector": "input[aria-label='Add a subject']", "value": "${subject}", "description": "Fill subject field"},
                {"action": "fill", "selector": "div[aria-label='Message body']", "value": "${body}", "description": "Fill body field"},
                {"action": "click", "selector": "button[aria-label='Send']", "description": "Click send button"}
            ]

class WebAutomationAgent:
    """Generic web automation agent for email services"""
    
    def __init__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.llm = LLMClient()
        
    def navigate_to_service(self, service: EmailService) -> None:
        """Navigate to the email service"""
        if service == EmailService.GMAIL:
            self.page.goto("https://mail.google.com")
            logger.info("Navigated to Gmail")
        else:  # Outlook
            self.page.goto("https://outlook.live.com")
            logger.info("Navigated to Outlook")
        
        # Wait for page to load
        self.page.wait_for_timeout(3000)
    
    def mock_authentication(self, service: EmailService) -> None:
        """Mock authentication process"""
        # In a real implementation, this would handle actual authentication
        logger.info(f"Mock authentication for {service.value}")
        self.page.wait_for_timeout(2000)  # Simulate auth time
    
    def execute_actions(self, actions: List[Dict], data: Dict) -> None:
        """Execute the generated actions"""
        for action in actions:
            try:
                action_type = action["action"]
                selector = action["selector"]
                description = action["description"]
                
                logger.info(f"Executing: {description}")
                
                if action_type == "click":
                    self.page.click(selector)
                elif action_type == "fill":
                    value = action["value"]
                    # Replace placeholders with actual data
                    for key, val in data.items():
                        value = value.replace(f"${{{key}}}", val)
                    self.page.fill(selector, value)
                
                self.page.wait_for_timeout(1000)  # Short delay between actions
                
            except Exception as e:
                logger.error(f"Failed to execute action: {action}, error: {e}")
                # In a real implementation, we'd have recovery logic here
    
    def send_email(self, instruction: str) -> None:
        """Main method to send email based on natural language instruction"""
        try:
            # Parse the instruction
            email_data = self.llm.parse_email_instruction(instruction)
            logger.info(f"Parsed email data: {email_data}")
            
            # Navigate to the service
            self.navigate_to_service(email_data.service)
            
            # Mock authentication
            self.mock_authentication(email_data.service)
            
            # Get HTML for UI analysis
            html = self.page.content()
            
            # Generate actions based on UI analysis
            actions = self.llm.analyze_ui_and_generate_actions(
                html, f"Send email using {email_data.service.value}"
            )
            
            # Prepare data for action execution
            data = {
                "recipient": email_data.recipient,
                "subject": email_data.subject,
                "body": email_data.body
            }
            
            # Execute the actions
            self.execute_actions(actions, data)
            
            logger.info("Email sent successfully!")
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
        finally:
            # Close browser
            self.page.wait_for_timeout(3000)  # Wait to see the result
            self.browser.close()
            self.playwright.stop()

class AutomationAPI:
    """FastAPI endpoint for the automation agent (conceptual)"""
    
    def __init__(self):
        self.agent = WebAutomationAgent()
    
    def send_email_endpoint(self, instruction: str) -> Dict:
        """Endpoint to send email based on instruction"""
        try:
            self.agent.send_email(instruction)
            return {"status": "success", "message": "Email sent successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def run_cli(self):
        """Simple CLI interface"""
        print("Humaein Web Automation Agent")
        print("Enter your email instruction (e.g., 'Send an email to test@example.com about the meeting using Gmail'):")
        
        instruction = input("> ")
        self.send_email_endpoint(instruction)

# Main execution
if __name__ == "__main__":
    # Example usage
    agent = WebAutomationAgent()
    
    # Test with different instructions
    instructions = [
        "Send an email to colleague@company.com about the project update using Gmail",
        "Send an email to friend@example.com about our weekend plans using Outlook"
    ]
    
    for instruction in instructions:
        print(f"\nProcessing: {instruction}")
        agent.send_email(instruction)
    
