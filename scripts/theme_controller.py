#!/usr/bin/env python3
"""
Theme Controller for Synchronized Video Generation
Provides easy theme switching and customization.
"""

import json
from pathlib import Path
from typing import Dict, Any

class ThemeController:
    def __init__(self):
        self.themes = {
            'energetic': {
                'name': 'Your Brand (Energetic)',
                'description': 'Gold/pink vibrant design with your current branding',
                'css_class': 'theme-energetic',
                'target_audience': 'General learners, engaging content',
                'file': 'themes/energetic.css'
            },
            'professional': {
                'name': 'Professional Academic',
                'description': 'Clean institutional design for business learners', 
                'css_class': 'theme-professional',
                'target_audience': 'Business professionals, corporate training',
                'file': 'themes/professional.css'
            },
            'minimalist': {
                'name': 'Minimalist Clean',
                'description': 'Simple, distraction-free design',
                'css_class': 'theme-minimalist', 
                'target_audience': 'Focus-oriented learners, accessibility',
                'file': 'themes/minimalist.css'
            },
            'german': {
                'name': 'German Cultural',
                'description': 'German flag colors and cultural elements',
                'css_class': 'theme-german',
                'target_audience': 'Cultural immersion, patriotic learners',
                'file': 'themes/german.css'
            }
        }
    
    def get_theme_info(self, theme_name: str) -> Dict[str, Any]:
        """Get information about a specific theme"""
        return self.themes.get(theme_name, {})
    
    def list_themes(self) -> Dict[str, Dict[str, Any]]:
        """List all available themes"""
        return self.themes
    
    def apply_theme_to_template(self, base_template_path: str, theme_name: str, output_path: str = None) -> str:
        """
        Apply a theme to the base template and return the themed template.
        """
        if theme_name not in self.themes:
            raise ValueError(f"Theme '{theme_name}' not found. Available: {list(self.themes.keys())}")
        
        theme_info = self.themes[theme_name]
        
        # Read base template
        with open(base_template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Load theme CSS
        theme_css_path = Path(theme_info['file'])
        if theme_css_path.exists():
            with open(theme_css_path, 'r', encoding='utf-8') as f:
                theme_css = f.read()
        else:
            print(f"⚠️ Theme CSS file not found: {theme_css_path}")
            theme_css = f"/* Theme CSS for {theme_name} not found */"
        
        # Apply theme
        themed_template = template_content.replace('{{theme_styles}}', theme_css)
        themed_template = themed_template.replace('{{theme_link}}', '')
        
        # Add theme class to container
        themed_template = themed_template.replace(
            'class="sync-container theme-container"',
            f'class="sync-container theme-container {theme_info["css_class"]}"'
        )
        
        # Save themed template if output path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(themed_template)
            
            print(f"✅ Themed template saved: {output_path}")
        
        return themed_template
    
    def generate_all_themed_templates(self, base_template_path: str, output_dir: str = 'templates/themed'):
        """
        Generate themed templates for all available themes.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        for theme_name, theme_info in self.themes.items():
            output_file = output_dir / f"teil1_{theme_name}.html"
            
            try:
                self.apply_theme_to_template(
                    base_template_path=base_template_path,
                    theme_name=theme_name,
                    output_path=output_file
                )
                generated_files.append(output_file)
                print(f"✅ Generated: {output_file}")
                
            except Exception as e:
                print(f"❌ Failed to generate {theme_name}: {e}")
        
        return generated_files
    
    def create_theme_report(self, output_file: str = 'theme_report.md'):
        """Create a markdown report of all available themes"""
        report_lines = [
            "# Available Video Themes",
            "",
            "This document describes all available themes for the Goethe video generation system.",
            ""
        ]
        
        for theme_name, theme_info in self.themes.items():
            report_lines.extend([
                f"## {theme_info['name']} (`{theme_name}`)",
                "",
                f"**Description:** {theme_info['description']}",
                f"**Target Audience:** {theme_info['target_audience']}",
                f"**CSS Class:** `{theme_info['css_class']}`",
                f"**CSS File:** `{theme_info['file']}`",
                "",
                "### Usage",
                f"```bash",
                f"# Generate with {theme_name} theme",
                f"python scripts/synchronized_pipeline.py input.json --theme {theme_name}",
                f"```",
                ""
            ])
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print(f"📄 Theme report created: {output_file}")
        return output_file


def setup_theme_system():
    """Set up the complete theme system"""
    print("🎨 Setting up theme system...")
    
    # Create theme directories
    theme_dirs = [
        'templates/themed',
        'themes',
        'templates/base'
    ]
    
    for directory in theme_dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    # Save base template
    base_template_path = Path('templates/base/teil1_base.html')
    print(f"💾 Save the base template as: {base_template_path}")
    
    # Save theme CSS files
    theme_files = {
        'themes/energetic.css': '/* Energetic theme CSS from artifact above */',
        'themes/professional.css': '/* Professional theme CSS from artifact above */',
        'themes/minimalist.css': '/* Minimalist theme CSS from artifact above */',
        'themes/german.css': '/* German theme CSS from artifact above */'
    }
    
    for file_path, content in theme_files.items():
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"📄 Created: {file_path}")
    
    print("✅ Theme system setup complete!")
    
    return ThemeController()


def main():
    """Demo the theme system"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Theme Controller for Goethe Videos')
    parser.add_argument('--setup', action='store_true', help='Set up theme system')
    parser.add_argument('--list-themes', action='store_true', help='List available themes')
    parser.add_argument('--generate-all', help='Generate all themed templates from base template')
    parser.add_argument('--apply-theme', nargs=3, metavar=('BASE', 'THEME', 'OUTPUT'), 
                       help='Apply theme: base_template theme_name output_file')
    parser.add_argument('--create-report', action='store_true', help='Create theme report')
    
    args = parser.parse_args()
    
    if args.setup:
        controller = setup_theme_system()
        return
    
    controller = ThemeController()
    
    if args.list_themes:
        print("🎨 Available Themes:")
        print("=" * 50)
        for theme_name, theme_info in controller.list_themes().items():
            print(f"📌 {theme_info['name']} ({theme_name})")
            print(f"   {theme_info['description']}")
            print(f"   Target: {theme_info['target_audience']}")
            print()
    
    elif args.generate_all:
        print("🎨 Generating all themed templates...")
        generated = controller.generate_all_themed_templates(args.generate_all)
        print(f"✅ Generated {len(generated)} themed templates")
    
    elif args.apply_theme:
        base_template, theme_name, output_file = args.apply_theme
        print(f"🎨 Applying theme '{theme_name}' to {base_template}")
        controller.apply_theme_to_template(base_template, theme_name, output_file)
    
    elif args.create_report:
        report_file = controller.create_theme_report()
        print(f"📄 Theme report created: {report_file}")
    
    else:
        print("Use --help for usage information")


if __name__ == "__main__":
    main()