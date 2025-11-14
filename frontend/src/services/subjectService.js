/**
 * Subject API Service
 *
 * Handles all API requests related to subject catalog browsing (US-2).
 * Public endpoint for viewing active technology monitoring subjects.
 */

import apiClient from './apiClient';

/**
 * Fetch paginated list of active subjects
 *
 * @param {number} page - Page number (default: 1)
 * @param {number} pageSize - Items per page (default: 50, max: 100)
 * @returns {Promise<Object>} Response with count, next, previous, and results
 *
 * Response format:
 * {
 *   count: 42,
 *   next: "http://localhost:8000/api/subjects/?page=2",
 *   previous: null,
 *   results: [
 *     {
 *       id: "550e8400-e29b-41d4-a716-446655440000",
 *       name: "AI and Machine Learning",
 *       description: "Latest developments in artificial intelligence...",
 *       status: "active"
 *     },
 *     ...
 *   ]
 * }
 */
export const fetchSubjects = async (page = 1, pageSize = 50) => {
  try {
    const response = await apiClient.get('/subjects/', {
      params: {
        page,
        page_size: pageSize,
      },
    });
    return response.data;
  } catch (error) {
    console.error('[subjectService] Error fetching subjects:', error);
    throw error;
  }
};

/**
 * Fetch all subjects by iterating through all pages
 *
 * @param {number} pageSize - Items per page (default: 100 for efficiency)
 * @returns {Promise<Array>} Array of all active subjects
 */
export const fetchAllSubjects = async (pageSize = 100) => {
  try {
    const allSubjects = [];
    let page = 1;
    let hasMore = true;

    while (hasMore) {
      const data = await fetchSubjects(page, pageSize);
      allSubjects.push(...data.results);

      // Check if there's a next page
      hasMore = data.next !== null;
      page++;
    }

    return allSubjects;
  } catch (error) {
    console.error('[subjectService] Error fetching all subjects:', error);
    throw error;
  }
};

export default {
  fetchSubjects,
  fetchAllSubjects,
};
