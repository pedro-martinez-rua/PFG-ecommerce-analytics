import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

import { Link } from '@/components/Link';
import { getReports } from '@/lib/api';
import { Report } from '@/lib/types';
import { EmptyState, PageLoading } from '@/components/shared';
import { FileText, Clock, ExternalLink } from 'lucide-react';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';

export function ReportsPage() {
  const { t } = useTranslation();

  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const loadReports = async () => {
      try {
        const data = await getReports();
        setReports(data);
      } finally {
        setLoading(false);
      }
    };
    loadReports();
  }, []);

  if (loading) {
    return <PageLoading message={t('reports.loading')} />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground mb-1">
          {t('reports.title')}
        </h1>
        <p className="text-muted-foreground">
          {t('reports.subtitle')}
        </p>
      </div>

      {reports.length === 0 ? (
        <EmptyState
          icon={FileText}
          title={t('reports.empty.title')}
          description={t('reports.empty.description')}
          action={{
            label: t('reports.empty.action'),
            onClick: () => navigate('/app/dashboards'),
          }}
        />
      ) : (
        <div className="bg-background rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t('reports.table.reportName')}</TableHead>
                <TableHead>{t('reports.table.dashboard')}</TableHead>
                <TableHead>{t('reports.table.kpiSummary')}</TableHead>
                <TableHead>{t('reports.table.created')}</TableHead>
                <TableHead className="w-[100px]"></TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {reports.map((report) => (
                <TableRow key={report.id}>
                  <TableCell className="font-medium">{report.name}</TableCell>
                  <TableCell className="text-muted-foreground">{report.dashboardName}</TableCell>
                  <TableCell className="text-muted-foreground">{report.kpiSummary}</TableCell>
                  <TableCell className="text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {new Date(report.createdAt).toLocaleDateString()}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Link href={`/app/dashboards/${report.dashboardId}`}>
                      <Button variant="ghost" size="sm" className="gap-1">
                        {t('reports.actions.open')}
                        <ExternalLink className="h-3 w-3" />
                      </Button>
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
