import { useNavigate } from 'react-router-dom';
import { ListChecks, ListTree, TrendingUp } from 'lucide-react';
import Button from '../../components/Button';

// Three primary navigation actions off this screen — sized a bit larger
// than a normal button since they're the main way to drill into a project.
export default function ProjectActionsRow({ projectId }) {
  const navigate = useNavigate();

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <Button
        variant="secondary"
        size="lg"
        onClick={() => navigate(`/projects/${projectId}/questions`)}
      >
        <ListChecks className="h-5 w-5" /> View All Questions
      </Button>

      <Button variant="secondary" size="lg" onClick={() => navigate(`/projects/${projectId}/topics`)}>
        <ListTree className="h-5 w-5" /> View All Topics
      </Button>

      <Button size="lg" onClick={() => navigate(`/projects/${projectId}/trends`)}>
        <TrendingUp className="h-5 w-5" /> Trend Analysis
      </Button>
    </div>
  );
}
