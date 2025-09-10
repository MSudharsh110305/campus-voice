import os
import sys
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from text_clean import clean_text, TextCleaner
from vectorizer import ComplaintVectorizer
from classifier import AuthorityClassifier  
from postprocess import PostProcessor

class CampusVoiceDemo:
    """
    Simple demo app for complaint classification pipeline.
    """
    
    def __init__(self):
        print("Campus Voice AI Demo - Initializing...")
        
        self.cleaner = TextCleaner()
        self.vectorizer = None
        self.classifier = None
        self.postprocessor = PostProcessor()
        
        self._setup_sample_model()
        
    def _setup_sample_model(self):
        print("Setting up sample model...")
        
        # Sample complaints for training
        sample_complaints = [
            "Room allotment process is taking too long and student queries are not answered properly",
            "Hostel gate timing restrictions are too strict for weekend college events",
            "The room hygiene is unacceptable, and the mess food quality has severely declined",
            "Hostel warden delayed action on multiple maintenance requests and student concerns",
            "Urgent: Water leakage in hostel bathroom is causing serious electrical hazards!",
            "Emergency hostel security breach, unauthorized persons entered building at night",
            "Examination results are being delayed beyond the announced schedule without proper communication",
            "Faculty member uses outdated teaching methods and refuses to adopt modern techniques",
            "Professor frequently cancels classes causing significant syllabus delay before exams",
            "HOD shows favoritism in academic evaluations and doesn't consider student feedback",
            "Ragging incident reported in the department; immediate action required for student safety",
            "Critical: Professor making discriminatory comments affecting students' mental health",
            "Canteen hygiene standards need improvement and food prices are too high for students",
            "Parking slots are overcrowded; no adequate space during peak college hours",
            "Wi-Fi connectivity issues in library and study areas disrupting academic work",
            "Sports ground maintenance is poor and equipment is damaged or missing",
            "Emergency! Main power supply in library has failed affecting all computer systems",
            "Unsafe structural damage noticed in main building stairs, immediate repair needed",
            "Hostel Wi-Fi and academic lab computer systems both are down affecting student studies",
            "Restrooms near department building are in poor condition affecting both faculty and students",
            "Deputy warden and HOD are both ignoring complaints; harassment case needs urgent attention",
            "Critical safety issue: Electrical problems in both hostel and academic building need immediate fix",
            "Student facing harassment from senior students in department, afraid to report publicly",
            "Bribery attempt by staff member for room allocation in hostel",
            "Discrimination based on background happening in canteen by staff members"
        ]
        
        cleaned_texts = [clean_text(text) for text in sample_complaints]
        
        sample_labels = [
            ["hostel"], ["hostel"],  # low priority hostel
            ["hostel"], ["hostel"],  # medium priority hostel
            ["hostel"], ["hostel"],  # high priority hostel
            ["academic"], ["academic"],  # low priority academic
            ["academic"], ["academic"],  # medium priority academic
            ["academic"], ["academic"],  # high priority academic
            ["infrastructure"], ["infrastructure"],  # low priority infrastructure
            ["infrastructure"], ["infrastructure"],  # medium priority infrastructure
            ["infrastructure"], ["infrastructure"],  # high priority infrastructure
            ["hostel", "infrastructure"], ["academic", "infrastructure"],  # multi-label medium priority
            ["hostel", "academic"], ["hostel", "infrastructure"],  # multi-label high priority
            ["academic"], ["hostel"], ["infrastructure"]  # privacy sensitive high priority
        ]
        
        print("Training vectorizer...")
        self.vectorizer = ComplaintVectorizer()
        X_train = self.vectorizer.fit_transform(cleaned_texts)
        
        print("Training classifier...")
        self.classifier = AuthorityClassifier()
        self.classifier.fit(X_train, sample_labels)
        
        print("Model setup complete.")
        
    def classify_complaint(self, complaint_text: str) -> Dict:
        print(f"\nProcessing complaint: '{complaint_text}'")
        
        cleaned = clean_text(complaint_text)
        print(f"Cleaned text: '{cleaned}'")
        
        X = self.vectorizer.transform([cleaned])
        print(f"Vectorized into {X.shape[1]} features")
        
        scores = self.classifier.predict_proba(X)[0]
        print(f"Scores - hostel: {scores[0]:.3f}, academic: {scores[1]:.3f}, infrastructure: {scores[2]:.3f}")
        
        result = self.postprocessor.process(scores)
        
        privacy = self._determine_privacy(complaint_text, result.authorities)
        priority = self._determine_priority(complaint_text)
        
        return {
            "complaint": complaint_text,
            "cleaned": cleaned,
            "authorities": result.authorities,
            "confidence_level": result.confidence_level,
            "confidences": result.confidences,
            "who_can_see": privacy["who_can_see"], 
            "privacy_level": privacy["level"],
            "priority": priority,
            "routing_notes": result.notes,
            "fallback_used": result.fallback_applied
        }
    
    def _determine_privacy(self, text: str, authorities: List[str]) -> Dict:
        text_lower = text.lower()
        sensitive_keywords = ["harassment", "ragging", "bribery", "abuse", "discrimination"]
        
        if any(word in text_lower for word in sensitive_keywords):
            return {
                "level": "private", 
                "who_can_see": "Only authorities and superiors"
            }
        
        authority_mentions = ["warden", "deputy warden", "hod", "professor", "ao"]
        mentioned = [auth for auth in authority_mentions if auth in text_lower]
        
        if mentioned:
            return {
                "level": "private",
                "who_can_see": f"Authorities higher than {mentioned[0]}"
            }
        
        return {
            "level": "public",
            "who_can_see": "Assigned authorities + public voting"
        }
    
    def _determine_priority(self, text: str) -> Dict:
        text_lower = text.lower()
        urgency_words = ["urgent", "emergency", "immediate", "critical", "serious", "unsafe"]
        urgency_count = sum(1 for word in urgency_words if word in text_lower)
        
        if urgency_count >= 2:
            return {"level": "high", "reason": f"Contains {urgency_count} urgency indicators"}
        elif urgency_count == 1:
            return {"level": "medium", "reason": f"Contains {urgency_count} urgency indicator"}
        else:
            return {"level": "low", "reason": "No urgency indicators found"}

def main():
    print("=" * 60)
    print("Campus Voice AI - Complaint Classifier Demo")
    print("=" * 60)
    
    demo = CampusVoiceDemo()
    
    default_complaints = [
        "Room allotment process is taking too long and student queries are not answered properly",
        "Hostel gate timing restrictions are too strict for weekend college events",
        "The room hygiene is unacceptable, and the mess food quality has severely declined",
        "Hostel warden delayed action on multiple maintenance requests and student concerns",
        "Urgent: Water leakage in hostel bathroom is causing serious electrical hazards!",
        "Emergency hostel security breach, unauthorized persons entered building at night",
        "Examination results are being delayed beyond the announced schedule without proper communication",
        "Faculty member uses outdated teaching methods and refuses to adopt modern techniques",
        "Professor frequently cancels classes causing significant syllabus delay before exams",
        "HOD shows favoritism in academic evaluations and doesn't consider student feedback",
        "Ragging incident reported in the department; immediate action required for student safety",
        "Critical: Professor making discriminatory comments affecting students' mental health",
        "Canteen hygiene standards need improvement and food prices are too high for students",
        "Parking slots are overcrowded; no adequate space during peak college hours",
        "Wi-Fi connectivity issues in library and study areas disrupting academic work",
        "Sports ground maintenance is poor and equipment is damaged or missing",
        "Emergency! Main power supply in library has failed affecting all computer systems",
        "Unsafe structural damage noticed in main building stairs, immediate repair needed",
        "Hostel Wi-Fi and academic lab computer systems both are down affecting student studies",
        "Restrooms near department building are in poor condition affecting both faculty and students",
        "Deputy warden and HOD are both ignoring complaints; harassment case needs urgent attention",
        "Critical safety issue: Electrical problems in both hostel and academic building need immediate fix",
        "Student facing harassment from senior students in department, afraid to report publicly",
        "Bribery attempt by staff member for room allocation in hostel",
        "Discrimination based on background happening in canteen by staff members"
    ]
    
    print("\nTesting default complaints:")
    print("-" * 60)
    
    for i, complaint in enumerate(default_complaints, 1):
        print(f"\nTest Case {i}:")
        result = demo.classify_complaint(complaint)
        print(f"Authorities: {', '.join(result['authorities'])}")
        print(f"Privacy Level: {result['privacy_level']} ({result['who_can_see']})")
        print(f"Priority: {result['priority']['level']} - {result['priority']['reason']}")
        print(f"Confidence: {result['confidence_level']}")
        if result['routing_notes']:
            print(f"Notes: {', '.join(result['routing_notes'])}")
    
    print("\nEnter your own complaints or type 'quit' to exit.")
    
    while True:
        try:
            complaint = input("\nEnter complaint: ").strip()
            if complaint.lower() in ['quit', 'exit', 'q']:
                print("Exiting. Thank you!")
                break
            
            if not complaint:
                print("Please enter a valid complaint.")
                continue
            
            result = demo.classify_complaint(complaint)
            
            print("\nClassification Results")
            print("-" * 50)
            print(f"Authorities to Handle: {', '.join(result['authorities'])}")
            print(f"Privacy Level: {result['privacy_level']}")
            print(f"Who Can See: {result['who_can_see']}")
            print(f"Priority: {result['priority']['level']} ({result['priority']['reason']})")
            print(f"AI Confidence: {result['confidence_level']}")
            print("Detailed Scores:")
            for auth, score in result['confidences'].items():
                print(f"  {auth}: {score:.3f}")
            if result['routing_notes']:
                print(f"Notes: {', '.join(result['routing_notes'])}")
        except KeyboardInterrupt:
            print("\nExiting. Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
