"""Text diffing functionality for Track Changes Editor"""

import difflib
import logging
import re
from typing import List, Dict, Any, Tuple, Optional

from .constants import MAX_GAP_SIZE, MERGE_GAP_SIZE


class TextDiffer:
    """Advanced diff algorithm to identify individual changes"""
    
    def __init__(self):
        self.differ = difflib.SequenceMatcher()
    
    def tokenize(self, text: str) -> List[str]:
        """Split text into words while preserving whitespace info and respecting line boundaries"""
        if not text:
            return []
        try:
            # Split on newlines first to ensure line boundaries are preserved
            lines = text.split('\n')
            tokens = []
            
            for i, line in enumerate(lines):
                if line:  # Non-empty line
                    # Tokenize the line content, filtering out empty tokens
                    line_tokens = [token for token in re.findall(r'\S+|\s+', line) if token]
                    tokens.extend(line_tokens)
                
                # Add newline token if not the last line
                if i < len(lines) - 1:
                    tokens.append('\n')
            
            # Filter out any empty tokens that might have been created
            return [token for token in tokens if token]
        except Exception as e:
            logging.error(f"Error tokenizing text: {e}")
            return [text]  # Fallback to single token
    
    def _find_sentence_boundaries(self, tokens: List[str]) -> set:
        """Identify sentence boundaries in the token list, including newlines"""
        boundaries = set()
        sentence_endings = {'.', '!', '?'}
        sentence_endings_with_space = {'. ', '! ', '? ', '.\n', '!\n', '?\n'}
        
        for i, token in enumerate(tokens):
            # Newlines are always sentence boundaries
            if token == '\n':
                boundaries.add(i + 1)
            # Traditional sentence endings
            elif (token.strip() in sentence_endings or
                  token in sentence_endings_with_space):
                boundaries.add(i + 1)
        return boundaries
    
    def _should_merge_groups(self, current_group: Dict, gap_start: int, gap_end: int,
                           sentence_boundaries: set, tokens: List[str]) -> bool:
        """Determine if groups should be merged based on gap analysis"""
        # Check if there's a newline in the gap - if so, never merge
        for i in range(gap_start, gap_end):
            if i < len(tokens) and tokens[i] == '\n':
                return False
        
        gap_crosses_sentence = any(
            boundary > gap_start and boundary <= gap_end
            for boundary in sentence_boundaries
        )
        gap_size = gap_end - gap_start
        return not gap_crosses_sentence or gap_size <= MERGE_GAP_SIZE
    
    def _group_changes(self, opcodes: List[Tuple], sentence_boundaries: set, original_tokens: List[str]) -> List[Dict]:
        """Group changes intelligently based on sentence boundaries and newlines"""
        grouped_changes = []
        current_group = None
        
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'equal':
                if current_group is not None:
                    crosses_sentence = any(boundary >= i1 and boundary <= i2
                                         for boundary in sentence_boundaries)
                    is_long_gap = (i2 - i1) > MAX_GAP_SIZE
                    
                    if crosses_sentence or is_long_gap:
                        grouped_changes.append(current_group)
                        current_group = None
                continue
            
            if current_group is None:
                current_group = {
                    'type': tag,
                    'original_start': i1,
                    'original_end': i2,
                    'suggested_start': j1,
                    'suggested_end': j2,
                    'operations': [(tag, i1, i2, j1, j2)]
                }
            else:
                if self._should_merge_groups(current_group, current_group['original_end'], i1, sentence_boundaries, original_tokens):
                    current_group['original_end'] = i2
                    current_group['suggested_end'] = j2
                    current_group['operations'].append((tag, i1, i2, j1, j2))
                    if tag != current_group['type']:
                        current_group['type'] = 'mixed'
                else:
                    grouped_changes.append(current_group)
                    current_group = {
                        'type': tag,
                        'original_start': i1,
                        'original_end': i2,
                        'suggested_start': j1,
                        'suggested_end': j2,
                        'operations': [(tag, i1, i2, j1, j2)]
                    }
        
        if current_group:
            grouped_changes.append(current_group)
        
        return grouped_changes
    
    def _determine_change_type(self, group: Dict, original_chunk: str, suggested_chunk: str) -> str:
        """Determine the primary change type for a group"""
        if group['type'] == 'mixed':
            if original_chunk.strip() and suggested_chunk.strip():
                return 'replace'
            elif suggested_chunk.strip() and not original_chunk.strip():
                return 'insert'
            elif original_chunk.strip() and not suggested_chunk.strip():
                return 'delete'
            else:
                return 'replace'
        return group['type']
    
    def get_changes(self, original_text: str, suggested_text: str) -> List[Dict[str, Any]]:
        """Returns list of grouped changes with positions"""
        try:
            # Handle empty inputs
            if not original_text and not suggested_text:
                return []
            
            original_tokens = self.tokenize(original_text or "")
            suggested_tokens = self.tokenize(suggested_text or "")
            
            self.differ.set_seqs(original_tokens, suggested_tokens)
            opcodes = self.differ.get_opcodes()
            
            sentence_boundaries = self._find_sentence_boundaries(original_tokens)
            grouped_changes = self._group_changes(opcodes, sentence_boundaries, original_tokens)
            
            changes = []
            for group in grouped_changes:
                original_chunk = ''.join(
                    original_tokens[group['original_start']:group['original_end']]
                )
                suggested_chunk = ''.join(
                    suggested_tokens[group['suggested_start']:group['suggested_end']]
                )
                
                change_type = self._determine_change_type(group, original_chunk, suggested_chunk)
                
                # Only include changes that have meaningful content
                if original_chunk.strip() or suggested_chunk.strip():
                    changes.append({
                        'type': change_type,
                        'original': original_chunk,
                        'suggested': suggested_chunk,
                        'position': (group['original_start'], group['original_end']),
                        'status': 'pending'
                    })
            
            return changes
            
        except Exception as e:
            logging.error(f"Error generating changes: {e}")
            return []