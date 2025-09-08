#!/usr/bin/env python3
"""
Teil Configuration System for Goethe Video Generation
Centralized configuration management for different Teil types
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class TeilConfigManager:
    def __init__(self, config_dir: str = 'config/teil'):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._configs = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Load all Teil configuration files"""
        for config_file in self.config_dir.glob('teil*.yaml'):
            teil_num = int(config_file.stem.replace('teil', ''))
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self._configs[teil_num] = yaml.safe_load(f)
                print(f"Loaded config for Teil {teil_num}")
            except Exception as e:
                print(f"Error loading {config_file}: {e}")
    
    def get_config(self, teil: int) -> Dict[str, Any]:
        """Get configuration for a specific Teil"""
        if teil not in self._configs:
            print(f"Warning: No config found for Teil {teil}, using Teil 1 defaults")
            return self._configs.get(1, self._get_default_config())
        return self._configs[teil]
    
    def get_timing_config(self, teil: int) -> Dict[str, float]:
        """Get timing configuration for a Teil"""
        config = self.get_config(teil)
        return config.get('timing', {})
    
    def get_audio_config(self, teil: int) -> Dict[str, Any]:
        """Get audio configuration for a Teil"""
        config = self.get_config(teil)
        return config.get('audio', {})
    
    def get_visual_config(self, teil: int) -> Dict[str, Any]:
        """Get visual/template configuration for a Teil"""
        config = self.get_config(teil)
        return config.get('visual', {})
    
    def get_structure_config(self, teil: int) -> Dict[str, Any]:
        """Get content structure configuration for a Teil"""
        config = self.get_config(teil)
        return config.get('structure', {})
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Fallback default configuration"""
        return {
            'timing': {
                'thinking_time': 5.0,
                'pause_between_plays': 3.0,
                'transition_duration': 2.5
            },
            'audio': {
                'play_count': 2,
                'engines': ['generative', 'neural', 'standard']
            },
            'visual': {
                'template': 'teil1_base.html',
                'theme': 'energetic'
            }
        }

# Configuration file generator
def create_teil_configs():
    """Create all Teil configuration files"""
    config_dir = Path('config/teil')
    config_dir.mkdir(parents=True, exist_ok=True)
    
    configs = {
        1: {
            'name': 'Teil 1 - Short Monologues',
            'description': 'Five short texts with multiple choice questions',
            
            'timing': {
                # Core timing
                'thinking_time': 5.0,          # User preference: shortened from 25s
                'pause_between_plays': 3.0,    # Pause between first and second play
                'transition_duration': 2.5,    # Minimum transition time
                'answer_reveal_pause': 2.0,    # Pause after showing answer
                
                # Section-specific timing
                'intro_duration': 15.0,        # Max intro duration
                'instructions_pause': 1.0,     # Pause after instructions
                'outro_duration': 15.0,        # Max outro duration
                
                # Task-specific
                'task_setup_pause': 0.5,       # Brief pause before text starts
                'question_to_answer_pause': 1.0  # Pause between question and answer reveal
            },
            
            'audio': {
                # Playback settings
                'text_play_count': 2,           # Play each text twice
                'question_play_count': 1,       # Play questions once
                'instruction_play_count': 1,    # Play instructions once
                
                # Voice preferences by role
                'voice_preferences': {
                    'instructor': {'gender': 'female', 'primary_voice': 'Marlene'},
                    'service_provider': {'gender': 'mixed', 'distribution': 'balanced'},
                    'customer': {'gender': 'mixed', 'distribution': 'balanced'},
                    'announcer': {'gender': 'female', 'primary_voice': 'Vicki'}
                },
                
                # Engine preferences
                'engine_hierarchy': ['generative', 'neural', 'standard'],
                'fallback_strategy': 'cascade',
                
                # Audio processing
                'sample_rate': '22050',
                'format': 'mp3',
                'normalize_volume': True
            },
            
            'visual': {
                # Template settings
                'base_template': 'teil1_base.html',
                'default_theme': 'energetic',
                'available_themes': ['energetic', 'professional', 'minimalist', 'german'],
                
                # Display settings
                'show_question_numbers': True,
                'show_progress_bar': True,
                'show_timer': False,           # No timer for non-exam mode
                'transition_animations': True,
                
                # Layout
                'content_display_mode': 'combined',  # Text + question together
                'answer_reveal_mode': 'immediate',   # Show answer right after thinking time
                
                # Visual elements
                'background_style': 'gradient',
                'font_size': 'medium',
                'contrast_mode': 'normal'
            },
            
            'structure': {
                # Content organization
                'sections': [
                    {'type': 'intro', 'required': True},
                    {'type': 'instructions', 'required': True},
                    {'type': 'combined_tasks', 'count': 5, 'required': True},
                    {'type': 'outro', 'required': True}
                ],
                
                # Task structure
                'task_pattern': [
                    'transition',
                    'combined_task',  # Text (2x) + Question + Thinking
                    'answer_reveal'
                ],
                
                # Content requirements
                'text_length_range': [30, 40],     # Words
                'question_options': 3,             # a, b, c
                'required_contexts': [             # Ensure variety
                    'service_announcement',
                    'business_message', 
                    'public_announcement',
                    'personal_message',
                    'weather_news'
                ]
            },
            
            'educational': {
                # Learning objectives
                'skill_focus': 'basic_comprehension',
                'cefr_level': 'A2',
                'vocabulary_complexity': 'everyday',
                
                # Assessment
                'passing_score': 0.6,              # 60% for A2
                'feedback_mode': 'immediate',       # Show answers immediately
                'mistake_analysis': False,          # Keep simple for A2
                
                # Adaptation
                'difficulty_adaptive': False,      # Fixed A2 level
                'speed_options': ['normal'],       # No speed variation for now
                'repeat_options': True             # Allow replay
            }
        },
        
        2: {
            'name': 'Teil 2 - Long Conversation + Visual Questions',
            'description': 'One long conversation followed by visual multiple choice',
            
            'timing': {
                'thinking_time': 20.0,          # Longer for complex content
                'conversation_play_count': 1,   # Play once only
                'visual_question_time': 25.0,   # Time to examine images
                'transition_duration': 3.0,
                'answer_reveal_pause': 3.0
            },
            
            'audio': {
                'conversation_play_count': 1,
                'question_play_count': 1,
                'dialogue_pause_between_speakers': 0.4,
                'natural_conversation_flow': True,
                
                'voice_preferences': {
                    'dialogue_speakers': {'gender': 'mixed', 'distinct_voices': True},
                    'instructor': {'gender': 'female', 'primary_voice': 'Marlene'}
                }
            },
            
            'visual': {
                'base_template': 'teil2_visual.html',
                'default_theme': 'professional',  # Better for visual questions
                'image_display_mode': 'large',
                'question_layout': 'visual_grid',
                'show_conversation_transcript': False  # Audio only
            },
            
            'structure': {
                'sections': [
                    {'type': 'intro', 'required': True},
                    {'type': 'instructions', 'required': True},
                    {'type': 'conversation', 'length': '2-3 minutes', 'required': True},
                    {'type': 'visual_questions', 'count': 5, 'required': True},
                    {'type': 'outro', 'required': True}
                ],
                
                'conversation_structure': {
                    'min_exchanges': 15,
                    'max_duration': 180,  # 3 minutes max
                    'speaker_count': 2,
                    'context_types': ['apartment_search', 'service_inquiry', 'planning_meeting']
                }
            }
        },
        
        3: {
            'name': 'Teil 3 - Short Dialogues + Visual Questions',
            'description': 'Five short conversations with visual answers',
            
            'timing': {
                'thinking_time': 15.0,           # Medium length
                'dialogue_play_count': 2,        # Play twice like Teil 1
                'pause_between_plays': 3.0,
                'visual_question_time': 20.0,
                'transition_duration': 2.5
            },
            
            'audio': {
                'dialogue_play_count': 2,
                'short_conversation_length': [30, 45],  # Seconds
                'speaker_variety': True,          # Different speakers per dialogue
                
                'voice_preferences': {
                    'dialogue_speakers': {'gender': 'mixed', 'rotation': 'balanced'},
                    'service_contexts': ['shop', 'restaurant', 'office', 'public_space']
                }
            },
            
            'visual': {
                'base_template': 'teil3_visual.html',
                'default_theme': 'minimalist',    # Clean for multiple dialogues
                'image_display_mode': 'medium',
                'dialogue_counter': True,
                'context_indicators': True        # Show where conversation happens
            },
            
            'structure': {
                'sections': [
                    {'type': 'intro', 'required': True},
                    {'type': 'instructions', 'required': True},
                    {'type': 'short_dialogues', 'count': 5, 'required': True},
                    {'type': 'outro', 'required': True}
                ],
                
                'dialogue_pattern': [
                    'dialogue_intro',
                    'short_dialogue',  # 2x play
                    'visual_question',
                    'answer_reveal'
                ]
            }
        },
        
        4: {
            'name': 'Teil 4 - Interview + Text Questions',
            'description': 'Long interview with traditional text-based questions',
            
            'timing': {
                'thinking_time': 30.0,           # Longest for complex analysis
                'interview_play_count': 1,       # Single play only
                'question_spacing': 15.0,        # Time between questions
                'analysis_time': 45.0,           # Time to process interview
                'transition_duration': 3.0
            },
            
            'audio': {
                'interview_play_count': 1,
                'interview_length': [240, 300],  # 4-5 minutes
                'question_play_count': 1,
                'complex_vocabulary': True,
                
                'voice_preferences': {
                    'interviewer': {'gender': 'female', 'professional_tone': True},
                    'interviewee': {'gender': 'mixed', 'natural_speech': True},
                    'instructor': {'gender': 'female', 'clear_diction': True}
                }
            },
            
            'visual': {
                'base_template': 'teil4_interview.html',
                'default_theme': 'professional',  # Serious tone for interviews
                'show_interview_progress': True,
                'question_display_mode': 'text_focus',
                'background_complexity': 'minimal'  # Keep focus on content
            },
            
            'structure': {
                'sections': [
                    {'type': 'intro', 'required': True},
                    {'type': 'instructions', 'required': True},
                    {'type': 'interview', 'length': '4-5 minutes', 'required': True},
                    {'type': 'processing_time', 'duration': 45, 'required': True},
                    {'type': 'text_questions', 'count': 8, 'required': True},
                    {'type': 'outro', 'required': True}
                ],
                
                'interview_structure': {
                    'topic_complexity': 'personal_experience',
                    'vocabulary_level': 'B1_bridge',  # Slightly harder
                    'speech_rate': 'natural',
                    'accent_variety': 'standard_german'
                }
            }
        }
    }
    
    # Create YAML files for each Teil
    for teil_num, config in configs.items():
        config_file = config_dir / f'teil{teil_num}.yaml'
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print(f"Created config/teil/teil{teil_num}.yaml")
    
    # Create a master index file
    index_file = config_dir / 'index.yaml'
    index_data = {
        'available_teile': list(configs.keys()),
        'config_version': '1.0',
        'last_updated': '2024-12-19',
        'description': 'Goethe A2 Teil configuration system'
    }
    
    with open(index_file, 'w', encoding='utf-8') as f:
        yaml.dump(index_data, f, default_flow_style=False)
    
    print(f"Created config/teil/index.yaml")
    print("Configuration system ready!")

# Integration helper
def get_timing_for_audio_generator(teil: int) -> Dict[str, float]:
    """Get timing configuration formatted for audio generator"""
    manager = TeilConfigManager()
    timing = manager.get_timing_config(teil)
    
    return {
        'thinking_time': timing.get('thinking_time', 5.0),
        'pause_between_plays': timing.get('pause_between_plays', 3.0),
        'transition_duration': timing.get('transition_duration', 2.5),
        'answer_reveal_pause': timing.get('answer_reveal_pause', 2.0),
        'task_setup_pause': timing.get('task_setup_pause', 0.5)
    }

def get_audio_settings_for_generator(teil: int) -> Dict[str, Any]:
    """Get audio configuration formatted for audio generator"""
    manager = TeilConfigManager()
    audio = manager.get_audio_config(teil)
    
    return {
        'text_play_count': audio.get('text_play_count', 2),
        'question_play_count': audio.get('question_play_count', 1),
        'engine_hierarchy': audio.get('engine_hierarchy', ['generative', 'neural', 'standard']),
        'voice_preferences': audio.get('voice_preferences', {}),
        'sample_rate': audio.get('sample_rate', '22050'),
        'format': audio.get('format', 'mp3')
    }

def get_template_settings_for_generator(teil: int, theme: str = None) -> Dict[str, Any]:
    """Get visual configuration for video generator"""
    manager = TeilConfigManager()
    visual = manager.get_visual_config(teil)
    
    return {
        'base_template': visual.get('base_template', f'teil{teil}_base.html'),
        'theme': theme or visual.get('default_theme', 'energetic'),
        'available_themes': visual.get('available_themes', ['energetic']),
        'show_progress_bar': visual.get('show_progress_bar', True),
        'transition_animations': visual.get('transition_animations', True),
        'content_display_mode': visual.get('content_display_mode', 'combined')
    }

if __name__ == "__main__":
    # Create all configuration files
    create_teil_configs()
    
    # Test the system
    manager = TeilConfigManager()
    
    print("\nTesting configuration system:")
    for teil in [1, 2, 3, 4]:
        timing = get_timing_for_audio_generator(teil)
        print(f"Teil {teil} thinking time: {timing['thinking_time']}s")
    
    print("\nConfiguration system created successfully!")
    print("Files created in: config/teil/")
    print("- teil1.yaml (your current A2 settings)")
    print("- teil2.yaml (conversation + visual)")  
    print("- teil3.yaml (short dialogues + visual)")
    print("- teil4.yaml (interview + text)")
    print("- index.yaml (master index)")
