# Todo List Extension

Full-featured Todoist task management with support for projects, sections, priorities, due dates, and filtering.

## Features

- **Project Management**: List and work with Todoist projects
- **Section Support**: Organize tasks within project sections
- **Task Operations**: Create, read, update, and complete tasks
- **Advanced Filtering**: Use Todoist's powerful filter syntax
- **Rich Metadata**: Access project names, section names, priorities, and due dates
- **Full CRUD**: Complete control over your task list

## Tools

### TODOLIST_GET_list_projects
List all Todoist projects.

**Example**: "List my Todoist projects"

**Response**: Returns array of projects with IDs and names

### TODOLIST_GET_list_sections
List Todoist sections, optionally filtered by project.

**Example**: "List sections in project 123"

**Parameters**:
- `project_id`: Optional project ID to filter sections

**Response**: Returns array of sections with IDs and names

### TODOLIST_GET_task_by_id
Get a single task by ID with enriched project and section information.

**Example**: "Show task 123 details"

**Parameters**:
- `task_id`: The task ID to retrieve

**Response**: Full task object with project and section names

### TODOLIST_GET_list_tasks
List active tasks with optional Todoist filter syntax.

**Example**: "Show my tasks for today"

**Parameters**:
- `filter`: Optional Todoist filter query (e.g., "today | overdue", "priority 1", "@home")

**Response**: Array of tasks enriched with project and section names

**Common Filters**:
- `today` - Tasks due today
- `overdue` - Overdue tasks
- `today | overdue` - Due today or overdue
- `priority 1` - P1 tasks
- `@label` - Tasks with specific label
- `#project` - Tasks in specific project

### TODOLIST_ACTION_create_task
Create a new Todoist task.

**Example**: "Create a task: 'Buy milk' in Inbox for today"

**Parameters**:
- `content` (required): Task title
- `project_id` (required): Project ID
- `section_id`: Optional section ID
- `description`: Optional task description
- `priority`: Priority level (1-4, where 4 is highest)
- `due_string`: Natural language due date ("today", "tomorrow", "next monday")
- `due_date`: Specific date in YYYY-MM-DD format
- `due_datetime`: ISO8601 datetime for specific time

**Response**: Created task object

### TODOLIST_UPDATE_update_task
Update an existing task. Only provided fields are changed.

**Example**: "Update task 123 to due tomorrow at 9am"

**Parameters**:
- `task_id` (required): Task ID to update
- `content`: New task title
- `description`: New description
- `priority`: New priority (1-4)
- `due_string`: New due date (natural language)
- `due_date`: New due date (YYYY-MM-DD)
- `due_datetime`: New due datetime (ISO8601)
- `project_id`: Move to different project
- `section_id`: Move to different section

**Response**: Update confirmation with task ID

### TODOLIST_ACTION_complete_task
Mark a task as completed.

**Example**: "Complete task 123"

**Parameters**:
- `task_id`: The task ID to complete

**Response**: Completion confirmation

## Configuration

### Required Environment Variables

```
TODOIST_API_TOKEN=your-todoist-api-token
```

### Getting Your API Token

1. Go to Todoist Settings → Integrations → Developer
2. Copy your API token
3. Add to `.env` file

## Priority Levels

- `1`: Priority 4 (Highest/Red)
- `2`: Priority 3 (High/Orange)
- `3`: Priority 2 (Medium/Yellow)
- `4`: Priority 1 (Normal/White)

## Due Date Formats

### Natural Language (`due_string`)
- "today"
- "tomorrow"
- "next monday"
- "every monday"
- "in 3 days"

### Specific Date (`due_date`)
- "2024-12-25"

### Specific DateTime (`due_datetime`)
- "2024-12-25T09:00:00"
- "2024-12-25T14:30:00Z"

## Example Workflows

### Daily Review
```
User: "Show my tasks for today"
Assistant: Lists all tasks due today with projects and sections
```

### Quick Task Creation
```
User: "Add 'Review PR' to my Work project for tomorrow"
Assistant: Creates task with due date set to tomorrow
```

### Task Management
```
User: "Move task 123 to the Urgent section and set priority to highest"
Assistant: Updates task with new section and priority 1
```

### Filtering
```
User: "Show me all P1 tasks that are overdue"
Assistant: Uses filter "priority 1 & overdue" to fetch tasks
```

## Dependencies

- `pydantic`
- `python-dotenv` (optional)
- `urllib` (standard library)

Install via: `pip install pydantic python-dotenv`

## API Reference

This extension uses the Todoist REST API v2. For advanced filter syntax, see:
https://todoist.com/help/articles/introduction-to-filters-V98wIH

## Notes

- All tasks are automatically enriched with project and section names
- The extension handles both absolute IDs and natural language for dates
- Task completion is permanent - use archive if you need to recover tasks
- Filter syntax is very powerful - refer to Todoist documentation for advanced queries

