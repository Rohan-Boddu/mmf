# Main entry point explained (`main.py`)

## What does it do?
`main.py` serves as the user-facing Interface Layer for the MMF (Memory Model File) system. It proves that all our modular pieces work together in harmony, orchestrating the `Loader`, `Matcher`, `Runtime`, and `Learner` through continuous interactions.

## Key components for beginners:
1. **Dynamic Pathing & Archives (`os.path`)**: We use `os.path.abspath(__file__)` to find the exact location of the `.mmf` system dynamically. It points to `assistant_export.mmf`—the packaged portable ZIP archive of our system.
2. **Component Instantiation**: 
   - We initialize the `MMFLoader`, `TextMatcher`, and `MMFLearner`.
   - We construct our orchestrator (`MMFRuntime`) by passing it the loader and matcher.
3. **Continuous Interaction Loop**: We use a `while True` loop to act like a chat terminal. It continually prompts for `User> ` input and stops only when you type `quit` or `exit`.
4. **Handling Runtime Signals (Self-Learning)**: 
   - We ask the runtime to process the user's input: `response = runtime.query(q)`
   - If the runtime returns a dictionary where `type == "match"`, we cleanly print the AI's response.
   - If `type == "no_match"`, `main.py` manages the **Self-Learning Flow**. It prints `I don't know this yet. Teach me:`, waits for you to type the answer, and passes that correct answer directly into `learner.learn()`.
   - After learning, it calls `runtime.initialize()` again so the system reloads the newest memory dynamically!

## Separation of Concerns
Note that `main.py` is the *only* file containing `input()` or `print()` statements. By keeping all user interaction here, the core backend logic remains perfectly decoupled and production-ready for APIs or Web Apps.
