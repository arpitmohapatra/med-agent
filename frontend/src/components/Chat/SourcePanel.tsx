import React from 'react';
import { FileText, Loader2 } from 'lucide-react';
import { Source } from '../../types';
import SourceCard from './SourceCard';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { ScrollArea } from '../ui/scroll-area';
import { Separator } from '../ui/separator';

interface SourcePanelProps {
  sources: Source[];
  isLoading?: boolean;
  query?: string;
}

const SourcePanel: React.FC<SourcePanelProps> = ({
  sources,
  isLoading = false,
  query,
}) => {
  if (isLoading) {
    return (
      <div className="h-full p-4 space-y-4">
        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center space-x-2">
              <Loader2 className="w-5 h-5 text-primary animate-spin" />
              <CardTitle className="text-lg">Searching...</CardTitle>
            </div>
          </CardHeader>
        </Card>
        
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse border-0 shadow-sm">
              <CardContent className="p-4">
                <div className="flex items-center space-x-2 mb-3">
                  <div className="w-6 h-6 bg-muted rounded-full"></div>
                  <div className="h-4 bg-muted rounded flex-1"></div>
                </div>
                <div className="space-y-2">
                  <div className="h-3 bg-muted rounded"></div>
                  <div className="h-3 bg-muted rounded w-3/4"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!sources || sources.length === 0) {
    return (
      <div className="h-full p-4">
        <Card className="border-0 shadow-sm mb-4">
          <CardHeader className="pb-3">
            <div className="flex items-center space-x-2">
              <FileText className="w-5 h-5 text-muted-foreground" />
              <CardTitle className="text-lg">Sources</CardTitle>
            </div>
          </CardHeader>
        </Card>
        
        <Card className="border-dashed border-2 border-muted">
          <CardContent className="text-center py-12">
            <FileText className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
            <h3 className="text-sm font-medium text-foreground mb-2">No sources available</h3>
            <p className="text-sm text-muted-foreground">
              Sources will appear here when using RAG mode
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <Card className="border-0 shadow-sm m-4 mb-0">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <FileText className="w-5 h-5 text-primary" />
              <CardTitle className="text-lg">Sources</CardTitle>
              <Badge variant="secondary" className="animate-in zoom-in-50 duration-300">
                {sources.length}
              </Badge>
            </div>
          </div>
          
          {query && (
            <>
              <Separator className="my-2" />
              <p className="text-sm text-muted-foreground">
                Results for: <span className="font-medium text-foreground">"{query}"</span>
              </p>
            </>
          )}
        </CardHeader>
      </Card>

      {/* Sources List */}
      <ScrollArea className="flex-1 px-4">
        <div className="space-y-3 pb-4">
          {sources.map((source, index) => (
            <div 
              key={source.id}
              className="animate-in slide-in-from-bottom-4 duration-500"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <SourceCard
                source={source}
                index={index}
              />
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Footer Info */}
      <Card className="border-0 shadow-sm m-4 mt-0">
        <CardContent className="p-4">
          <div className="text-xs text-muted-foreground space-y-1">
            <p className="flex items-center gap-2">
              <span>📊</span> Sources ranked by relevance
            </p>
            <p className="flex items-center gap-2">
              <span>🔗</span> Click "View" to open full content
            </p>
            <p className="flex items-center gap-2">
              <span>⚕️</span> Information is for educational purposes
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SourcePanel;
