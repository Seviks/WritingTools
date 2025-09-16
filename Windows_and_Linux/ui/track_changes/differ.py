"""Text diffing functionality for Track Changes Editor"""

import difflib
import logging
import re
from typing import List, Dict, Any, Tuple, Optional

from .constants import MAX_GAP_SIZE, MERGE_GAP_SIZE


class TextDiffer:
    """Diff algorithm to identify individual changes"""
    
    def __init__(self):
        self.differ = difflib.SequenceMatcher()
    
    def tokenize(self, text: str) -> List[str]:
        """Split text into words while preserving whitespace info and respecting line boundaries"""
        if not text:
            return []
        try:
            lines = text.split('\n')
            tokens = []
            
            for i, line in enumerate(lines):
                if line:
                    line_tokens = [token for token in re.findall(r'\S+|\s+', line) if token]
                    tokens.extend(line_tokens)
                
                if i < len(lines) - 1:
                    tokens.append('\n')
            
            return [token for token in tokens if token]
        except Exception as e:
            logging.error(f"Error tokenizing text: {e}")
            return [text]
    
    def _find_sentence_boundaries(self, tokens: List[str]) -> set:
        """Identify sentence boundaries in the token list"""
        boundaries = set()
        
        for i, token in enumerate(tokens):
            if token == '\n':
                boundaries.add(i + 1)
            elif token and (token.endswith(('.', '!', '?')) or
                          token in {'. ', '! ', '? ', '.\n', '!\n', '?\n'}):
                boundaries.add(i + 1)
        return boundaries
    
    def _should_merge_groups(self, current_group: Dict, gap_start: int, gap_end: int,
                           sentence_boundaries: set, tokens: List[str]) -> bool:
        """Determine if groups should be merged based on gap analysis"""
        gap_size = gap_end - gap_start
        
        if gap_size <= MERGE_GAP_SIZE:
            return not any(tokens[i] == '\n' for i in range(gap_start, min(gap_end, len(tokens))))
        
        gap_range = set(range(gap_start + 1, gap_end + 1))
        gap_crosses_sentence = bool(sentence_boundaries & gap_range)
        has_newline = any(tokens[i] == '\n' for i in range(gap_start, min(gap_end, len(tokens))))
        
        return not (gap_crosses_sentence or has_newline)
    
    def _group_changes(self, opcodes: List[Tuple], sentence_boundaries: set, original_tokens: List[str]) -> List[Dict]:
        """Group changes intelligently based on sentence boundaries and newlines"""
        grouped_changes = []
        current_group = None
        
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'equal':
                if current_group is not None:
                    gap_range = set(range(i1, i2 + 1))
                    crosses_sentence = bool(sentence_boundaries & gap_range)
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
        if group['type'] != 'mixed':
            return group['type']
        
        has_original = bool(original_chunk.strip())
        has_suggested = bool(suggested_chunk.strip())
        
        if has_original and has_suggested:
            return 'replace'
        elif has_suggested:
            return 'insert'
        elif has_original:
            return 'delete'
        else:
            return 'replace'
    
    def get_changes(self, original_text: str, suggested_text: str) -> List[Dict[str, Any]]:
        """Returns list of grouped changes with positions"""
        try:
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