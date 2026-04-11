import os
import sys
# Resolve backend scope natively for legacy CLI commands
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from mmf.loader import MMFLoader
from mmf.matcher import TfidfMatcher
from mmf.runtime import MMFRuntime
from mmf.learner import MMFLearner

def main():
    # 1. Define the dynamic path to the MMF directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    mmf_dir = os.path.join(base_dir, 'assistant_export.mmf')

    # 2. Instantiate our components
    loader = MMFLoader(directory_path=mmf_dir)
    matcher = TfidfMatcher()
    learner = MMFLearner(directory_path=mmf_dir)

    # 3. Create and initialize the runtime
    runtime = MMFRuntime(loader=loader, matcher=matcher)
    
    try:
        runtime.initialize()
        print(f"Loaded System: {runtime.manifest.get('name')} v{runtime.manifest.get('version')}")
    except Exception as e:
        print(f"Failed to initialize runtime: {e}")
        return

    # 4. Interactive Test Loop
    print("\n--- Testing MMF v0.2 Learning System ---")
    print("Type 'quit' or 'exit' to stop.\n")
    
    while True:
        try:
            q = input("User> ").strip()
            if not q:
                continue
            if q.lower() in ['quit', 'exit']:
                break

            response = runtime.query(q)
            
            if response["type"] == "match":
                print(f"Assistant> {response['response']}\n")
                
            elif response["type"] == "no_match":
                # System signals learning is required
                print(f"Assistant> I don't know this yet. Teach me:")
                teach_input = input("Correct Response> ").strip()
                
                if teach_input:
                    try:
                        # Append via the learner module
                        learner.learn(query=q, response=teach_input)
                        print("Assistant> Learned successfully.\n")
                        
                        # System must reflect learned data after reload
                        runtime.initialize()
                    except Exception as learn_err:
                        print(f"Error during learning: {learn_err}\n")
                else:
                    print("Assistant> Learning aborted.\n")
                    
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
