/**
 * Subject Card Component
 *
 * Displays a single subject with name, description, and status.
 * Used in the SubjectCatalog page for browsing available monitoring topics.
 *
 * US-2: View Active Subject Catalog
 */

import PropTypes from 'prop-types';
import './SubjectCard.css';

const SubjectCard = ({ subject, onSubscribe }) => {
  const { id, name, description, status } = subject;

  return (
    <div className="subject-card">
      <div className="subject-card-header">
        <h3 className="subject-card-title">{name}</h3>
        <span className={`subject-card-status status-${status}`}>
          {status}
        </span>
      </div>

      <p className="subject-card-description">{description}</p>

      {onSubscribe && (
        <div className="subject-card-footer">
          <button
            className="subject-card-button"
            onClick={() => onSubscribe(id)}
            aria-label={`Subscribe to ${name}`}
          >
            Subscribe
          </button>
        </div>
      )}
    </div>
  );
};

SubjectCard.propTypes = {
  subject: PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    description: PropTypes.string.isRequired,
    status: PropTypes.string.isRequired,
  }).isRequired,
  onSubscribe: PropTypes.func, // Optional: will be used in US-3 for subscription
};

export default SubjectCard;
