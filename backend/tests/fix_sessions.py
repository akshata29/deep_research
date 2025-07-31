import json

# Read the sessions metadata file
with open('backend/sessions/sessions_metadata.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Fix all sessions - data is a list of sessions
for session in data:
    if 'search_tasks' in session:
        for task in session['search_tasks']:
            # Fix field name
            if 'researchGoal' in task:
                task['research_goal'] = task.pop('researchGoal')
            
            # Ensure all required fields exist
            if 'images' not in task:
                task['images'] = []
            if 'sources' not in task:
                task['sources'] = []
            if 'learning' not in task:
                task['learning'] = ""
            if 'state' not in task:
                task['state'] = "pending"
            if 'query' not in task:
                task['query'] = ""

# Write back the fixed data
with open('backend/sessions/sessions_metadata.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Fixed all researchGoal -> research_goal field names and ensured all required fields exist")
