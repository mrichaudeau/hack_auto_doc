/**
 * Subject Catalog Page Component
 *
 * Public browsing interface for viewing active technology monitoring subjects.
 * Displays paginated list of subjects with search and filtering capabilities.
 *
 * US-2: View Active Subject Catalog
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { fetchSubjects } from '../services/subjectService';
import SubjectCard from '../components/subjects/SubjectCard';
import Pagination from '../components/common/Pagination';
import Alert from '../components/common/Alert';
import './SubjectCatalogPage.css';

const SubjectCatalogPage = () => {
  const { isAuthenticated } = useAuth();

  // State management
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  // Fetch subjects from API
  useEffect(() => {
    const loadSubjects = async () => {
      try {
        setLoading(true);
        setError(null);

        console.log('[SubjectCatalog] Fetching subjects:', {
          page: currentPage,
          pageSize,
        });

        const data = await fetchSubjects(currentPage, pageSize);

        console.log('[SubjectCatalog] Subjects loaded:', {
          count: data.count,
          resultsLength: data.results.length,
        });

        setSubjects(data.results);
        setTotalCount(data.count);
        setTotalPages(Math.ceil(data.count / pageSize));
      } catch (err) {
        console.error('[SubjectCatalog] Error loading subjects:', err);
        setError(
          err.response?.data?.detail ||
            'Failed to load subjects. Please try again later.'
        );
      } finally {
        setLoading(false);
      }
    };

    loadSubjects();
  }, [currentPage, pageSize]);

  // Handle page change
  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    // Scroll to top when changing pages
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Handle page size change
  const handlePageSizeChange = (newPageSize) => {
    setPageSize(newPageSize);
    setCurrentPage(1); // Reset to first page
  };

  // Handle subscribe (placeholder for US-3)
  const handleSubscribe = (subjectId) => {
    console.log('[SubjectCatalog] Subscribe clicked for subject:', subjectId);
    // TODO: Implement subscription in US-3
    alert('Subscription feature will be available in US-3');
  };

  return (
    <div className="subject-catalog-page">
      <div className="subject-catalog-container">
        {/* Header */}
        <header className="subject-catalog-header">
          <div className="header-content">
            <h1 className="page-title">Available Monitoring Subjects</h1>
            <p className="page-subtitle">
              Browse and discover technology monitoring topics to stay updated
              on the latest trends
            </p>
          </div>

          {/* Navigation */}
          <nav className="header-nav">
            <Link to="/" className="nav-link">
              Home
            </Link>
            {isAuthenticated ? (
              <Link to="/dashboard" className="nav-link">
                Dashboard
              </Link>
            ) : (
              <>
                <Link to="/login" className="nav-link">
                  Sign In
                </Link>
                <Link to="/register" className="nav-button">
                  Get Started
                </Link>
              </>
            )}
          </nav>
        </header>

        {/* Error Alert */}
        {error && (
          <Alert type="error" message={error} onClose={() => setError(null)} />
        )}

        {/* Loading State */}
        {loading && (
          <div className="loading-container">
            <div className="spinner"></div>
            <p className="loading-text">Loading subjects...</p>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && subjects.length === 0 && (
          <div className="empty-state">
            <h2 className="empty-state-title">No subjects available</h2>
            <p className="empty-state-text">
              There are no active monitoring subjects at this time. Please check
              back later.
            </p>
          </div>
        )}

        {/* Subject Grid */}
        {!loading && !error && subjects.length > 0 && (
          <>
            <div className="subjects-grid">
              {subjects.map((subject) => (
                <SubjectCard
                  key={subject.id}
                  subject={subject}
                  onSubscribe={isAuthenticated ? handleSubscribe : null}
                />
              ))}
            </div>

            {/* Pagination */}
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              totalCount={totalCount}
              pageSize={pageSize}
              onPageChange={handlePageChange}
              onPageSizeChange={handlePageSizeChange}
              pageSizeOptions={[25, 50, 100]}
            />
          </>
        )}

        {/* Footer */}
        <footer className="subject-catalog-footer">
          <p className="footer-text">
            {isAuthenticated
              ? 'Subscribe to subjects to receive automated technology reports'
              : 'Sign in to subscribe to subjects and receive personalized reports'}
          </p>
        </footer>
      </div>
    </div>
  );
};

export default SubjectCatalogPage;
