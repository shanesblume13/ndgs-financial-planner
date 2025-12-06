# NDGS Financial Planner

A financial projection and scenario planning tool built with Streamlit.

## Features
- **10-Year Projections**: Detailed cash flow modeling for Store and Property entities.
- **Scenario Management**: Save and load different financial scenarios (Local JSON).
- **AI Consultant**: Integration with Google Gemini, OpenAI, and Anthropic for financial advice.

## Local Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ndgs-financial-planner
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Secrets (Optional for AI features):**
   - Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
   - Add your API keys.

4. **Run the app:**
   ```bash
   streamlit run app.py
   ```

## Deployment (Streamlit Cloud)

1. **Push to GitHub.**
2. **Connect to Streamlit Cloud:**
   - Select the repository and `app.py` as the main entry point.
3. **Configure Secrets:**
   - In the Streamlit Cloud dashboard, go to **Settings > Secrets**.
   - Copy the content of your local `secrets.toml` into the secrets area.
4. **Data Persistence Warning:**
   - This app runs on ephemeral file storage. 
   - **Important:** Scenarios saved to "Local JSON" will be lost if the app restarts or redeploys.
   - For a production deployment, consider connecting a database (Supabase, Firebase, or AWS).

## Project Structure
- `app.py`: Main entry point.
- `model.py`: Core financial logic and data classes.
- `views/`: UI components (Dashboard, Sidebar).
- `services/`: External integrations (AI Service).
- `utils/`: Utility functions (Storage).

## Testing

Run the test suite using the virtual environment's Python:
```bash
# If venv is active:
python -m unittest discover tests

# If venv is NOT active (direct path):
./.venv/bin/python -m unittest discover tests
```
