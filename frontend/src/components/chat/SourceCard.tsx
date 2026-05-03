import { FileText } from 'lucide-react';
import type { Source } from '../../types/api';

interface Props { source: Source; index: number; }

export default function SourceCard({ source, index }: Props) {
  return (
    <div className="source-card" title={source.citation}>
      <FileText size={11} className="source-card-icon" />
      <span>[{index}] {source.filename}</span>
    </div>
  );
}
