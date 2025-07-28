/**
 * Utility functions to parse JSON content from research responses and convert to markdown
 */

interface ParsedQuestions {
  section: string;
  questions: string[];
}

interface ParsedPlan {
  section: string;
  objectives?: string[];
  key_questions?: string[];
  methodology?: string;
  deliverables?: string[];
  sources_to_prioritize?: string[];
}

interface ParsedFindings {
  section: string;
  [key: string]: any;
}

/**
 * Try to parse JSON content, fallback to original string if not JSON
 */
export function tryParseJSON(content: string): any {
  try {
    return JSON.parse(content);
  } catch {
    return null;
  }
}

/**
 * Parse questions content and convert to markdown
 */
export function parseQuestionsToMarkdown(content: string): string {
  const parsed = tryParseJSON(content);
  
  if (parsed && parsed.questions && Array.isArray(parsed.questions)) {
    const { section, questions } = parsed as ParsedQuestions;
    
    let markdown = `# ${section}\n\n`;
    questions.forEach((question, index) => {
      markdown += `${index + 1}. ${question}\n\n`;
    });
    
    return markdown;
  }
  
  // Fallback to original content if not valid JSON
  return content;
}

/**
 * Parse research plan content and convert to markdown
 */
export function parsePlanToMarkdown(content: string): string {
  const parsed = tryParseJSON(content);
  
  if (parsed && parsed.section) {
    const plan = parsed as ParsedPlan;
    
    let markdown = `# ${plan.section}\n\n`;
    
    if (plan.objectives && plan.objectives.length > 0) {
      markdown += `## Objectives\n`;
      plan.objectives.forEach(obj => {
        markdown += `- ${obj}\n`;
      });
      markdown += `\n`;
    }
    
    if (plan.key_questions && plan.key_questions.length > 0) {
      markdown += `## Key Questions\n`;
      plan.key_questions.forEach(question => {
        markdown += `- ${question}\n`;
      });
      markdown += `\n`;
    }
    
    if (plan.methodology) {
      markdown += `## Methodology\n${plan.methodology}\n\n`;
    }
    
    if (plan.deliverables && plan.deliverables.length > 0) {
      markdown += `## Deliverables\n`;
      plan.deliverables.forEach(deliverable => {
        markdown += `- ${deliverable}\n`;
      });
      markdown += `\n`;
    }
    
    if (plan.sources_to_prioritize && plan.sources_to_prioritize.length > 0) {
      markdown += `## Sources to Prioritize\n`;
      plan.sources_to_prioritize.forEach(source => {
        markdown += `- ${source}\n`;
      });
      markdown += `\n`;
    }
    
    return markdown;
  }
  
  // Fallback to original content if not valid JSON
  return content;
}

/**
 * Parse research findings content and convert to markdown
 */
export function parseFindingsToMarkdown(content: string): string {
  const parsed = tryParseJSON(content);
  
  if (parsed && parsed.section) {
    const findings = parsed as ParsedFindings;
    
    let markdown = `# ${findings.section}\n\n`;
    
    // Handle specific known fields with better formatting
    const fieldsToDisplay = [
      'Company Snapshot',
      'Key Company Metrics', 
      'Sales Mix',
      'Revenue by Segment',
      'Businesses Overview',
      'Stock Graph History',
      'Considerations',
      'Third-Party Perspectives and Multiples',
      'Credit Perspectives',
      'Equity Perspectives',
      'Appendix'
    ];
    
    fieldsToDisplay.forEach(field => {
      if (findings[field]) {
        markdown += `## ${field}\n`;
        
        if (field === 'Considerations' && typeof findings[field] === 'object') {
          const considerations = findings[field];
          
          if (considerations.Strengths && Array.isArray(considerations.Strengths)) {
            markdown += `### Strengths\n`;
            considerations.Strengths.forEach((strength: string) => {
              markdown += `- ${strength}\n`;
            });
            markdown += `\n`;
          }
          
          if (considerations.Weaknesses && Array.isArray(considerations.Weaknesses)) {
            markdown += `### Weaknesses\n`;
            considerations.Weaknesses.forEach((weakness: string) => {
              markdown += `- ${weakness}\n`;
            });
            markdown += `\n`;
          }
          
          if (considerations.Opportunities && Array.isArray(considerations.Opportunities)) {
            markdown += `### Opportunities\n`;
            considerations.Opportunities.forEach((opportunity: string) => {
              markdown += `- ${opportunity}\n`;
            });
            markdown += `\n`;
          }
          
          if (considerations.Risks && Array.isArray(considerations.Risks)) {
            markdown += `### Risks\n`;
            considerations.Risks.forEach((risk: string) => {
              markdown += `- ${risk}\n`;
            });
            markdown += `\n`;
          }
        } else {
          markdown += `${findings[field]}\n\n`;
        }
      }
    });
    
    return markdown;
  }
  
  // Fallback to original content if not valid JSON
  return content;
}

/**
 * Parse final report content and ensure proper markdown formatting
 */
export function parseFinalReportToMarkdown(content: string): string {
  if (!content) return '';
  
  // Try to parse as JSON first
  const parsed = tryParseJSON(content);
  if (parsed && parsed.report) {
    return parsed.report;
  }
  
  // If it's already markdown or plain text, ensure it's properly formatted
  let markdown = content;
  
  // Clean up any JSON artifacts if present
  if (markdown.includes('{"') && markdown.includes('"}')) {
    // Try to extract markdown from JSON wrapper
    const jsonMatch = markdown.match(/(?:"report":\s*"([^"]*)")|(?:"content":\s*"([^"]*)")/);
    if (jsonMatch) {
      markdown = (jsonMatch[1] || jsonMatch[2]).replace(/\\n/g, '\n').replace(/\\"/g, '"');
    }
  }
  
  // Ensure proper spacing and formatting
  markdown = markdown
    .replace(/\n{3,}/g, '\n\n') // Replace multiple newlines with double newlines
    .replace(/^[\s]*#/gm, '#') // Ensure headers start at line beginning
    .replace(/\*\*(.*?)\*\*/g, '**$1**') // Ensure bold formatting
    .trim();
  
  return markdown;
}

/**
 * Extract individual questions from numbered text format
 * Example: "1. What is...?\n2. Should the research...?\n3. What level..."
 * Returns: ["What is...?", "Should the research...?", "What level..."]
 */
export function extractQuestionsFromText(content: string): string[] {
  // Split by numbered pattern and filter out empty strings
  const questions = content
    .split(/\d+\.\s+/)
    .filter(q => q.trim().length > 0)
    .map(q => q.trim().replace(/\n\s*$/, '')); // Remove trailing newlines
  
  return questions;
}

/**
 * Generic function to parse any research content based on phase
 */
export function parseResearchContent(content: string, phase?: string): string {
  if (!content) return '';
  
  switch (phase) {
    case 'questions':
      return parseQuestionsToMarkdown(content);
    case 'plan':
      return parsePlanToMarkdown(content);
    case 'execute':
      return parseFindingsToMarkdown(content);
    case 'final_report':
    case 'report':
      return parseFinalReportToMarkdown(content);
    default:
      // Try to auto-detect and parse, or return original content
      const parsed = tryParseJSON(content);
      if (parsed) {
        if (parsed.questions) return parseQuestionsToMarkdown(content);
        if (parsed.objectives || parsed.key_questions) return parsePlanToMarkdown(content);
        if (parsed.section === 'Research Findings') return parseFindingsToMarkdown(content);
        if (parsed.report) return parseFinalReportToMarkdown(content);
      }
      return parseFinalReportToMarkdown(content); // Default to final report parsing for better formatting
  }
}
