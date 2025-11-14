# Subject Catalog Management - Admin User Guide

**Version:** 1.0
**Last Updated:** 2025-01-15
**For:** Platform Administrators

## Overview

This guide explains how to manage the technology monitoring subject catalog using the Django Admin interface. Only administrators have access to create, modify, and archive subjects that users can subscribe to for automated content monitoring.

## Table of Contents

1. [Accessing the Admin Interface](#accessing-the-admin-interface)
2. [Creating a New Subject](#creating-a-new-subject)
3. [Managing Web Sources](#managing-web-sources)
4. [Modifying Subjects](#modifying-subjects)
5. [Archiving Subjects](#archiving-subjects)
6. [Bulk Operations](#bulk-operations)
7. [Searching and Filtering](#searching-and-filtering)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Accessing the Admin Interface

### Prerequisites
- Administrator account (staff + superuser privileges)
- Access to platform admin panel

### Steps
1. Navigate to: `http://localhost:8000/admin/` (or your deployment URL)
2. Log in with your administrator credentials
3. Click **"Subscriptions"** in the left sidebar
4. Click **"Subjects"** to access the subject catalog

---

## Creating a New Subject

### When to Create a Subject
Create a new subject when:
- Users request monitoring for a new technology topic
- A new technology trend emerges
- You want to expand the platform's coverage

### Steps

1. **Navigate to Subject List**
   - Go to `/admin/subscriptions/subject/`
   - Click the **"ADD SUBJECT"** button (top right)

2. **Fill in Subject Information**

   **Required Fields:**
   - **Name:** Unique subject name (e.g., "Kubernetes", "AI Ethics")
     - Max 200 characters
     - Must be unique (case-insensitive)
     - Use clear, recognizable names

   - **Description:** Detailed description of the technology topic
     - No length limit
     - Be descriptive to help users understand the subject
     - Include key aspects and scope

   **Optional Fields:**
   - **Status:** Choose "Active" or "Archived"
     - Default: Active
     - Active subjects are visible to users
     - Archived subjects are hidden

3. **Add Web Sources (Optional)**

   Scroll down to the **"Web Sources"** section:

   - Click **"Add another Web Source"** to add URLs
   - Enter valid URLs for content scraping:
     - Must start with `http://` or `https://`
     - Examples:
       - `https://kubernetes.io/blog/`
       - `https://github.com/kubernetes/kubernetes/releases`
   - Add as many sources as needed
   - You can leave web sources empty and add them later

4. **Save the Subject**
   - Click **"SAVE"** to create the subject
   - Or **"SAVE AND ADD ANOTHER"** to create multiple subjects
   - Or **"SAVE AND CONTINUE EDITING"** to keep editing

### Example: Creating "Kubernetes" Subject

```
Name: Kubernetes
Description: Container orchestration platform for automating deployment,
            scaling, and management of containerized applications.
Status: Active

Web Sources:
1. https://kubernetes.io/blog/
2. https://github.com/kubernetes/kubernetes/releases
3. https://www.cncf.io/blog/category/kubernetes/
```

---

## Managing Web Sources

### What are Web Sources?
Web sources are URLs that the platform's AI agents will scrape for content related to the subject. The Firecrawl service handles JavaScript-heavy sites.

### Adding Web Sources to Existing Subject

1. Open the subject for editing
2. Scroll to **"Web Sources"** section
3. Click **"Add another Web Source"**
4. Enter the URL
5. Click **"SAVE"**

### Removing Web Sources

1. Open the subject for editing
2. Find the web source in the inline list
3. Check the **"DELETE"** checkbox next to the URL
4. Click **"SAVE"**

### Web Source Best Practices

**Good URLs:**
- Official blogs and release pages
- GitHub release feeds
- Technology news sites
- Community forums and discussions

**Avoid:**
- Paywalled content
- Login-required pages
- Dynamic content that requires interaction
- Social media feeds (may have rate limits)

**URL Validation:**
- Platform validates URLs automatically (RFC 3986 compliance)
- Invalid URLs will show an error message
- Max URL length: 2048 characters

---

## Modifying Subjects

### Editing Subject Details

1. Navigate to subject list: `/admin/subscriptions/subject/`
2. Click the subject name or **"Edit"** icon
3. Modify fields as needed:
   - Name (must remain unique)
   - Description
   - Status
   - Web sources
4. Click **"SAVE"**

### Change History

Every change is tracked via **django-simple-history**:

1. Open a subject for editing
2. Click the **"HISTORY"** button (top right)
3. View all changes with:
   - Timestamp
   - User who made the change
   - Fields modified
   - Previous and new values

---

## Archiving Subjects

### When to Archive
Archive subjects when:
- Topic is no longer relevant
- Subject is temporarily inactive
- Testing is complete (for test subjects)
- Consolidating similar subjects

### Archiving a Single Subject

**Method 1: Edit and Save**
1. Open the subject
2. Change **Status** to "Archived"
3. Click **"SAVE"**

**Method 2: Delete (Soft Delete)**
1. Open the subject
2. Click **"DELETE"** button
3. Confirm deletion
   - **Note:** This is a soft delete - subject is archived, not permanently deleted

### Effects of Archiving
- Subject is hidden from user API endpoints
- Users cannot see or subscribe to archived subjects
- Existing subscriptions remain but no new content is generated
- Data is preserved for audit trail
- Can be reactivated at any time

### Reactivating Archived Subject

1. Filter list by "Archived" status (left sidebar)
2. Open the archived subject
3. Change **Status** to "Active"
4. Click **"SAVE"**

---

## Bulk Operations

### Archiving Multiple Subjects

1. Go to subject list
2. Check the checkboxes next to subjects you want to archive
3. Select **"Archive selected subjects"** from the action dropdown
4. Click **"GO"**
5. Confirm the action

### Reactivating Multiple Subjects

1. Filter list to show archived subjects
2. Check the checkboxes next to subjects to reactivate
3. Select **"Reactivate selected subjects"** from dropdown
4. Click **"GO"**
5. Confirm the action

---

## Searching and Filtering

### Searching

Use the **search bar** (top right) to search by:
- Subject name
- Description text

Example searches:
- `kubernetes` - finds "Kubernetes" subject
- `container` - finds all subjects with "container" in name/description

### Filtering

Use the **filters** in the left sidebar:

**By Status:**
- All (default)
- Active
- Archived

**By Date:**
- Today
- Past 7 days
- This month
- This year
- Date range

### Sorting

Click column headers to sort by:
- **Name** (A-Z or Z-A)
- **Created at** (newest or oldest first)
- **Subscribers** (most or least)
- **Status** (active first or archived first)

---

## Best Practices

### Subject Naming Conventions

**DO:**
- Use official technology names: "Kubernetes", "Docker"
- Be specific: "React 18" instead of just "React"
- Use proper capitalization: "Node.js" not "nodejs"

**DON'T:**
- Use generic names: "Programming", "Software"
- Include version numbers unless necessary
- Use abbreviations without context: "ML" → "Machine Learning"

### Description Guidelines

**Good Description:**
```
Kubernetes is an open-source container orchestration platform for
automating deployment, scaling, and management of containerized
applications. Covers releases, best practices, security updates,
and community developments.
```

**Poor Description:**
```
Container stuff
```

### Web Source Selection

**Quality over Quantity:**
- 3-5 authoritative sources better than 20 mediocre ones
- Prioritize official sources
- Verify URLs work before adding

**Source Diversity:**
- Official documentation
- Project blogs/releases
- Community discussions
- Industry news

---

## Troubleshooting

### Common Issues

#### Issue: "Subject with this name already exists"

**Cause:** Subject names must be unique (case-insensitive)

**Solution:**
- Check if similar subject already exists
- Use filtering/search to find it
- Consider if you need a new subject or should reactivate archived one
- Add distinguishing details: "Python 3.12" vs "Python"

#### Issue: "Enter a valid URL"

**Cause:** Invalid URL format in web source

**Solution:**
- Ensure URL starts with `http://` or `https://`
- Remove spaces and special characters
- Check for typos
- Test URL in browser first

#### Issue: Can't delete subject

**Cause:** You're trying to permanently delete (not possible)

**Solution:**
- Use archive function instead (soft delete)
- Subject data is preserved for audit trail
- If truly need to remove, contact system administrator

#### Issue: Subject not visible to users

**Possible Causes:**
1. Status is "Archived"
2. Just created (users may need to refresh)
3. API cache (rare)

**Solution:**
1. Check status is "Active"
2. Wait 30 seconds for cache
3. Check API directly: `GET /api/admin/subjects/`

#### Issue: Web sources not being scraped

**Note:** Web scraping happens asynchronously via Celery workers

**Check:**
1. Web sources are valid URLs
2. Sites are accessible (not blocked)
3. Celery workers are running
4. Check logs for scraping errors

---

## API Access (Advanced)

Administrators can also use the REST API:

### Endpoints

```
GET    /api/admin/subjects/      # List all subjects
POST   /api/admin/subjects/      # Create subject
GET    /api/admin/subjects/{id}/ # Get subject details
PATCH  /api/admin/subjects/{id}/ # Update subject
DELETE /api/admin/subjects/{id}/ # Archive subject
```

### Authentication

Include JWT token in header:
```
Authorization: Bearer <your-access-token>
```

### Example: Create Subject via API

```bash
curl -X POST http://localhost:8000/api/admin/subjects/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Docker",
    "description": "Container platform",
    "status": "active",
    "web_sources": [
      {"url": "https://docker.com/blog/"}
    ]
  }'
```

### API Documentation

- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- OpenAPI Schema: `http://localhost:8000/api/schema/`

---

## Security Notes

### Access Control

- Only administrators (staff + superuser) can manage subjects
- Regular users have read-only access via public API
- All changes are logged with user ID and timestamp

### Audit Trail

All subject modifications are tracked:
- Who made the change
- What was changed
- When it was changed
- Previous and new values

To view audit trail:
1. Open subject in admin
2. Click **"HISTORY"** button
3. Review change log

### URL Validation

Platform validates all web source URLs for security:
- Blocks javascript: protocol
- Blocks file:// protocol
- Validates RFC 3986 compliance
- Max length: 2048 characters

---

## Performance Tips

### For Large Catalogs (100+ subjects)

1. **Use Filters**
   - Filter by status to reduce list size
   - Use date filters for recent subjects

2. **Use Search**
   - Search is faster than scrolling
   - Use specific terms

3. **Pagination**
   - List shows 50 subjects per page
   - Use pagination controls at bottom

### API Performance

- List endpoint: < 200ms for 1000+ subjects
- Create endpoint: < 500ms with web sources
- Optimized with database indexing and query prefetching

---

## Support

### Getting Help

**For technical issues:**
- Check this guide first
- Review error messages carefully
- Check system logs

**For access issues:**
- Verify you have admin privileges
- Contact system administrator

**For feature requests:**
- Submit via internal ticketing system
- Include use case and examples

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-15 | Initial version |

---

**End of Guide**
