/**Task Templates Component - Quick templates for common tasks*/
import React from 'react';

export const TASK_TEMPLATES = {
  feature: { priority: 'P1', effort: 'M', template: 'Add [feature name] — Implement [description]' },
  bugfix: { priority: 'P0', effort: 'S', template: 'Fix [bug] — Resolve [issue]' },
  refactor: { priority: 'P2', effort: 'M', template: 'Refactor [component] — Improve [aspect]' },
  test: { priority: 'P1', effort: 'S', template: 'Test [module] — Add tests for [functionality]' },
  docs: { priority: 'P2', effort: 'S', template: 'Document [feature] — Add documentation' }
};

export const TaskTemplates: React.FC = () => (
  <div>{Object.keys(TASK_TEMPLATES).map(k => <button key={k}>{k}</button>)}</div>
);
