import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, FolderOpen } from 'lucide-react';
import AppShell from '../../components/AppShell';
import Button from '../../components/Button';
import EmptyState from '../../components/EmptyState';
import { useApiData } from '../../hooks/useApiData';
import { listProjects, getProjectSummary } from '../../services/projectsService';
import ProjectsStatsRow from './ProjectsStatsRow';
import ProjectsToolbar from './ProjectsToolbar';
import ProjectsTable from './ProjectsTable';
import NewProjectModal from './NewProjectModal';

// The list endpoint doesn't include the per-project counts the table needs,
// so we fetch each project's summary alongside it (fine at this app's scale)
// and merge the two into one row per project.
async function fetchProjectsWithCounts() {
  const projects = await listProjects();
  const summaries = await Promise.all(projects.map((project) => getProjectSummary(project.id)));

  return projects.map((project, index) => ({
    ...project,
    created_by: summaries[index].created_by,
    total_question_papers: summaries[index].total_question_papers,
    total_syllabi: summaries[index].total_syllabi,
    total_subjects: summaries[index].total_subjects,
    total_questions: summaries[index].total_questions,
  }));
}

export default function ProjectsDashboard() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchProjects = useCallback(() => fetchProjectsWithCounts(), []);
  const { data: projects, isLoading, error } = useApiData(fetchProjects);

  const filteredProjects = useMemo(() => {
    if (!projects) return [];
    const query = search.trim().toLowerCase();
    if (!query) return projects;
    return projects.filter((project) => project.name.toLowerCase().includes(query));
  }, [projects, search]);

  return (
    <AppShell breadcrumb={[{ label: 'Projects' }]}>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-text-primary">Projects</h1>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus className="h-4 w-4" /> New Project
        </Button>
      </div>

      <div className="mt-6">
        <ProjectsStatsRow />
      </div>

      {isLoading && <p className="mt-8 text-sm text-text-muted">Loading projects…</p>}

      {error && (
        <p className="mt-8 text-sm text-critical">Couldn't load projects: {error.message}</p>
      )}

      {!isLoading && !error && projects && projects.length === 0 && (
        <div className="mt-6 rounded-card bg-surface shadow-card">
          <EmptyState
            icon={FolderOpen}
            message="No projects yet. Create one to get started."
            actionLabel="+ New Project"
            onAction={() => setIsModalOpen(true)}
          />
        </div>
      )}

      {!isLoading && !error && projects && projects.length > 0 && (
        <>
          <div className="mt-6 max-w-sm">
            <ProjectsToolbar searchValue={search} onSearchChange={setSearch} />
          </div>

          <div className="mt-4">
            {filteredProjects.length > 0 ? (
              <ProjectsTable
                projects={filteredProjects}
                onRowClick={(row) => navigate(`/projects/${row.id}`)}
              />
            ) : (
              <p className="py-8 text-center text-sm text-text-muted">
                No projects match “{search}”.
              </p>
            )}
          </div>
        </>
      )}

      <NewProjectModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </AppShell>
  );
}
