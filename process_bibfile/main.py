import re
import os
import click
import difflib
from datetime import datetime

# Configuration for venue-specific checks
# Each dictionary specifies:
# - name: Common name of the venue.
# - search_terms_in_field: Regex patterns to detect the venue in 'booktitle' or 'journal' fields.
# - expected_entry_type: The correct BibTeX @type (e.g., 'inproceedings', 'article').
# - expected_field_key_in_bib: The field where the venue name should be (e.g., 'booktitle', 'journal').
# - recommended_field_value_string: The suggested full field string (e.g., "booktitle = {Full Name}").
# - description_for_issue: A short description for error messages (e.g., "ICCV会议论文").
VENUE_CONFIG = [
    # Conferences
    {
        "name": "ICLR",
        "search_terms_in_field": [r"International\s+Conference\s+on\s+Learning\s+Representations\b"],
        "expected_entry_type": "inproceedings",
        "expected_field_key_in_bib": "booktitle",
        "recommended_field_value_string": "booktitle = {International Conference on Learning Representations}",
        "description_for_issue": "ICLR会议论文"
    },
    {
        "name": "CVPR",
        "search_terms_in_field": [r"Conference\s+on\s+Computer\s+Vision\s+and\s+Pattern\s+Recognition\b"],
        "expected_entry_type": "inproceedings",
        "expected_field_key_in_bib": "booktitle",
        "recommended_field_value_string": "booktitle = {Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition}",
        "description_for_issue": "CVPR会议论文"
    },
    {
        "name": "ICCV",
        "search_terms_in_field": [
            r"International\s+Conference\s+on\s+Computer\s+Vision\b(?!\s*,\s*Image\s+and\s+Deep\s+Learning)",
            r"\\bICCV\\b"
        ],
        "expected_entry_type": "inproceedings",
        "expected_field_key_in_bib": "booktitle",
        "recommended_field_value_string": "booktitle = {Proceedings of the IEEE/CVF International Conference on Computer Vision}",
        "description_for_issue": "ICCV会议论文"
    },
    {
        "name": "ECCV",
        "search_terms_in_field": [r"European\s+Conference\s+on\s+Computer\s+Vision\b", r"\\bECCV\\b"],
        "expected_entry_type": "inproceedings",
        "expected_field_key_in_bib": "booktitle",
        "recommended_field_value_string": "booktitle = {European Conference on Computer Vision}",
        "description_for_issue": "ECCV会议论文"
    },
    {
        "name": "NeurIPS",
        "search_terms_in_field": [
            r"Neural\s+Information\s+Processing\s+Systems\b",
            r"\\bNIPS\\b",
            r"\\bNeurIPS\\b",
            r"Adv\\.\\s+Neural\\s+Inform\\.\\s+Process\\.\\s+Syst\\."
        ],
        "expected_entry_type": "inproceedings",
        "expected_field_key_in_bib": "booktitle",
        "recommended_field_value_string": "booktitle = {Advances in Neural Information Processing Systems}",
        "description_for_issue": "NeurIPS会议论文"
    },
    {
        "name": "ICML",
        "search_terms_in_field": [r"International\s+Conference\s+on\s+Machine\s+Learning\b", r"\\bICML\\b"],
        "expected_entry_type": "inproceedings",
        "expected_field_key_in_bib": "booktitle",
        "recommended_field_value_string": "booktitle = {International Conference on Machine Learning}",
        "description_for_issue": "ICML会议论文"
    },
    {
        "name": "AAAI",
        "search_terms_in_field": [r"AAAI\s+Conference\s+on\s+Artificial\s+Intelligence\b", r"\\bAAAI\\b(?!\\w)"],
        "expected_entry_type": "inproceedings",
        "expected_field_key_in_bib": "booktitle",
        "recommended_field_value_string": "booktitle = {Proceedings of the AAAI Conference on Artificial Intelligence}",
        "description_for_issue": "AAAI会议论文"
    },
    {
        "name": "IJCAI",
        "search_terms_in_field": [r"International\s+Joint\s+Conference\s+on\s+Artificial\s+Intelligence\b", r"\\bIJCAI\\b"],
        "expected_entry_type": "inproceedings",
        "expected_field_key_in_bib": "booktitle",
        "recommended_field_value_string": "booktitle = {Proceedings of the International Joint Conference on Artificial Intelligence}",
        "description_for_issue": "IJCAI会议论文"
    },
    {
        "name": "SIGGRAPH",
        "search_terms_in_field": [
            r"\\bSIGGRAPH\\b",
            r"Special\s+Interest\s+Group\s+on\s+Computer\s+Graphics\s+and\s+Interactive\s+Techniques\b"
        ],
        "expected_entry_type": "inproceedings",
        "expected_field_key_in_bib": "booktitle",
        "recommended_field_value_string": "booktitle = {ACM SIGGRAPH Conference Proceedings}", # Year typically included
        "description_for_issue": "SIGGRAPH会议论文"
    },
    {
        "name": "ACMMM",
        "search_terms_in_field": [r"ACM\s+Int\.\s+Conf\.\s+Multimedia\b", r"\bACMMM\b", r"\bACM\s+Multimedia\b"],
        "expected_entry_type": "inproceedings",
        "expected_field_key_in_bib": "booktitle",
        "recommended_field_value_string": "booktitle = {Proceedings of the ACM International Conference on Multimedia}",
        "description_for_issue": "ACMMM会议论文"
    },
    {
        "name": "ACL",
        "search_terms_in_field": [r"Association\s+for\s+Computational\s+Linguistics\b", r"\bACL\b"],
        "expected_entry_type": "inproceedings",
        "expected_field_key_in_bib": "booktitle",
        "recommended_field_value_string": "booktitle = {Proceedings of the Association for Computational Linguistics}",
        "description_for_issue": "ACL会议论文"
    },
    {
        "name": "MICCAI",
        "search_terms_in_field": [r"Medical\s+Image\s+Computing\s+and\s+Computer-Assisted\s+Intervention\b", r"\bMICCAI\b"],
        "expected_entry_type": "inproceedings",
        "expected_field_key_in_bib": "booktitle",
        "recommended_field_value_string": "booktitle = {Medical Image Computing and Computer-Assisted Intervention}",
        "description_for_issue": "MICCAI会议论文"
    },
    {
        "name": "CVIDL",
        "search_terms_in_field": [r"Computer\s+Vision\s+Image\s+and\s+Deep\s+Learning\b", r"\bCVIDL\b"],
        "expected_entry_type": "inproceedings",
        "expected_field_key_in_bib": "booktitle",
        "recommended_field_value_string": "booktitle = {International Conference on Computer Vision, Image and Deep Learning}",
        "description_for_issue": "CVIDL会议论文"
    },
    # Journals
    {
        "name": "PAMI",
        "search_terms_in_field": [
            r"IEEE\s+Transactions\s+on\s+Pattern\s+Analysis\s+and\s+Machine\s+Intelligence\b",
            r"IEEE\s+Trans\\.\\s+Pattern\\s+Anal\\.\\s+Mach\\.\\s+Intell\\.",
            r"\\bTPAMI\\b", r"\\bPAMI\\b"
        ],
        "expected_entry_type": "article",
        "expected_field_key_in_bib": "journal",
        "recommended_field_value_string": "journal = {IEEE Transactions on Pattern Analysis and Machine Intelligence}",
        "description_for_issue": "PAMI期刊论文"
    },
    {
        "name": "IJCV",
        "search_terms_in_field": [
            r"International\s+Journal\s+of\s+Computer\s+Vision\b",
            r"Int\\.\\s+J\\.\\s+Comput\\.\\s+Vis\\.",
            r"\\bIJCV\\b"
        ],
        "expected_entry_type": "article",
        "expected_field_key_in_bib": "journal",
        "recommended_field_value_string": "journal = {International Journal of Computer Vision}",
        "description_for_issue": "IJCV期刊论文"
    },
    {
        "name": "TIP",
        "search_terms_in_field": [
            r"IEEE\s+Transactions\s+on\s+Image\s+Processing\b",
            r"IEEE\s+Trans\\.\\s+Image\\s+Process\\.",
            r"\\bTIP\\b"
        ],
        "expected_entry_type": "article",
        "expected_field_key_in_bib": "journal",
        "recommended_field_value_string": "journal = {IEEE Transactions on Image Processing}",
        "description_for_issue": "TIP期刊论文"
    },
    {
        "name": "TOG",
        "search_terms_in_field": [
            # Avoid matching if it's clearly a SIGGRAPH proceeding in TOG
            r"ACM\s+Transactions\s+on\s+Graphics(?!\\s*\\(TOG\\)\\s*-\\s*Proceedings\\s+of\\s+ACM\\s+SIGGRAPH)",
            r"ACM\s+Trans\\.\\s+Graph\\.(?!\\s*\\(TOG\\)\\s*-\\s*Proceedings\\s+of\\s+ACM\\s+SIGGRAPH)",
            r"\\bTOG\\b"
        ],
        "expected_entry_type": "article",
        "expected_field_key_in_bib": "journal",
        "recommended_field_value_string": "journal = {ACM Transactions on Graphics}",
        "description_for_issue": "TOG期刊论文"
    },
    {
        "name": "JMLR",
        "search_terms_in_field": [r"Journal\s+of\s+Machine\s+Learning\s+Research\b", r"\bJMLR\b"],
        "expected_entry_type": "article",
        "expected_field_key_in_bib": "journal",
        "recommended_field_value_string": "journal = {Journal of Machine Learning Research}",
        "description_for_issue": "JMLR期刊论文"
    },
    {
        "name": "TKDE",
        "search_terms_in_field": [r"IEEE\s+Transactions\s+on\s+Knowledge\s+and\s+Data\s+Engineering\b", r"\bTKDE\b"],
        "expected_entry_type": "article",
        "expected_field_key_in_bib": "journal",
        "recommended_field_value_string": "journal = {IEEE Transactions on Knowledge and Data Engineering}",
        "description_for_issue": "TKDE期刊论文"
    },
    {
        "name": "Neurocomputing",
        "search_terms_in_field": [r"\bNeurocomputing\b"],
        "expected_entry_type": "article",
        "expected_field_key_in_bib": "journal",
        "recommended_field_value_string": "journal = {Neurocomputing}",
        "description_for_issue": "Neurocomputing期刊论文"
    }
]

def check_and_fix_bib_file(file_path, auto_fix=False):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        entry_pattern = r'@(\w+)\s*\{([^@]*?)(?=@|\Z)'
        entries = re.findall(entry_pattern, content, re.DOTALL)
        
        issues = []
        fixed_entries = []
        
        def extract_value_content_from_field_str(field_str_with_key_and_value):
            """Extracts content from "key = {content}" or "key = \"content\"" """
            match = re.search(r"\w+\s*=\s*[\{\"]((?:.|\n)*?)[\}\"]", field_str_with_key_and_value)
            return match.group(1).strip() if match else None

        for i, (current_entry_type_str, current_entry_content_str) in enumerate(entries):
            original_entry = f"@{current_entry_type_str}{{{current_entry_content_str}"
            modified_entry = original_entry
            has_changes = False
            
            key_match = re.match(r'([^,]+),', current_entry_content_str)
            entry_key = key_match.group(1).strip() if key_match else f"未知条目 #{i+1}"
            
            processed_by_venue_check = False
            for venue_conf in VENUE_CONFIG:
                core_pattern_str = "|".join(f"(?:{term})" for term in venue_conf["search_terms_in_field"])
                venue_mention_regex = rf"(journal|booktitle)\s*=\s*[\{{\"]\s*.*?(?:{core_pattern_str}).*?\s*[\}}\"]"
                mention_match = re.search(venue_mention_regex, current_entry_content_str, re.IGNORECASE | re.DOTALL)
                
                if mention_match:
                    field_key_from_bib = mention_match.group(1).lower()
                    
                    current_field_full_str_match = re.search(
                        rf"({re.escape(field_key_from_bib)}\s*=\s*[\{{\"](?:.|\n)*?[\}}\"])",
                        current_entry_content_str,
                        re.IGNORECASE
                    )
                    current_field_full_str_from_bib = current_field_full_str_match.group(1) if current_field_full_str_match else ""

                    current_value_content_from_bib = extract_value_content_from_field_str(current_field_full_str_from_bib)
                    recommended_value_content = extract_value_content_from_field_str(venue_conf["recommended_field_value_string"])

                    value_is_non_standard = False
                    if current_value_content_from_bib is not None and recommended_value_content is not None:
                        norm_current = ' '.join(current_value_content_from_bib.replace('\\n', ' ').split())
                        norm_recomm = ' '.join(recommended_value_content.replace('\\n', ' ').split())
                        if norm_current != norm_recomm:
                            value_is_non_standard = True
                    
                    type_is_wrong = current_entry_type_str.lower() != venue_conf["expected_entry_type"].lower()
                    key_is_wrong = field_key_from_bib != venue_conf["expected_field_key_in_bib"].lower()

                    issue_found_for_venue = False
                    fix_description_parts = []

                    if type_is_wrong:
                        issue_found_for_venue = True
                        fix_description_parts.append(f"类型应为 @{venue_conf['expected_entry_type']}")
                    
                    if key_is_wrong:
                        issue_found_for_venue = True
                        fix_description_parts.append(f"字段应为 {venue_conf['recommended_field_value_string']}")
                    elif value_is_non_standard: # Key is correct, but value is non-standard
                        issue_found_for_venue = True
                        fix_description_parts.append(f"{venue_conf['expected_field_key_in_bib']} 字段内容应为 {{{recommended_value_content}}}")

                    if issue_found_for_venue:
                        issue_msg_base = f"建议: '{entry_key}' ({venue_conf['description_for_issue']})"
                        issues.append(f"{issue_msg_base} {', '.join(fix_description_parts)}.")
                        
                        if auto_fix:
                            # 1. Fix type if wrong
                            if type_is_wrong:
                                modified_entry = modified_entry.replace(
                                    f"@{current_entry_type_str}{{", 
                                    f"@{venue_conf['expected_entry_type']}{{", 
                                    1
                                )
                                has_changes = True

                            # 2. Fix field key and/or value
                            if key_is_wrong:
                                current_modified_content_match = re.match(r"@\w+\s*\{(.*)\}", modified_entry, re.DOTALL)
                                if current_modified_content_match: # Should always match
                                    entry_content_being_modified = current_modified_content_match.group(1)
                                    
                                    incorrect_field_pattern_to_remove = rf"\b{re.escape(field_key_from_bib)}\s*=\s*[\{{\"](?:.|\n)*?[\}}\"],?\s*"
                                    entry_content_being_modified = re.sub(
                                        incorrect_field_pattern_to_remove, "", entry_content_being_modified,
                                        count=1, flags=re.IGNORECASE
                                    ).strip()

                                    parts = entry_content_being_modified.split(',', 1)
                                    bib_item_key_part = parts[0].strip()
                                    remaining_fields_part = parts[1].strip() if len(parts) > 1 else ""
                                    
                                    new_field_str = venue_conf["recommended_field_value_string"]
                                    
                                    if remaining_fields_part:
                                        entry_content_being_modified = f"{bib_item_key_part},\n  {new_field_str},\n  {remaining_fields_part}"
                                    else:
                                        entry_content_being_modified = f"{bib_item_key_part},\n  {new_field_str}"
                                    
                                    entry_content_being_modified = re.sub(r",\s*$", "", entry_content_being_modified.strip())
                                    entry_content_being_modified = re.sub(r",\s*(?=\w+\s*=\s*[\{\"])", ",\n  ", entry_content_being_modified) # ensure space after comma and indent for fields
                                    entry_content_being_modified = re.sub(r"\n\s*\n", "\n", entry_content_being_modified)

                                    current_type_of_modified_entry = re.match(r"@(\w+)\s*\{", modified_entry).group(1)
                                    modified_entry = f"@{current_type_of_modified_entry}{{{entry_content_being_modified}}}"
                                    has_changes = True
                            
                            elif value_is_non_standard: # Key was correct, value is non-standard
                                field_to_standardize_pattern = rf"\b{re.escape(venue_conf['expected_field_key_in_bib'])}\s*=\s*[\{{\"](?:.|\n)*?[\}}\"]"
                                modified_entry = re.sub(
                                    field_to_standardize_pattern,
                                    venue_conf["recommended_field_value_string"],
                                    modified_entry,
                                    count=1, flags=re.IGNORECASE
                                )
                                has_changes = True
                    
                    processed_by_venue_check = True
                    break 
            
            if processed_by_venue_check and has_changes:
                fixed_entries.append((original_entry, modified_entry, entry_key))
                continue # Skip generic checks if a specific venue rule was applied
                
            # Generic checks (if not handled by a specific venue rule)
            # 检查 @inproceedings 是否包含 booktitle
            if current_entry_type_str.lower() == 'inproceedings':
                if 'booktitle' not in current_entry_content_str.lower():
                    issues.append(f"错误: '{entry_key}' (@inproceedings) 缺少 'booktitle' 字段")
                    # Cannot auto-fix this - would need to know what booktitle to add
                
                if re.search(r"\bjournal\s*=", current_entry_content_str, re.IGNORECASE):
                    issues.append(f"警告: '{entry_key}' (@inproceedings) 包含 'journal' 字段，应该使用 'booktitle'")
                    
                    if auto_fix:
                        # Find the journal field value
                        journal_match = re.search(r"journal\s*=\s*([\{\"].*?[\}\"])", current_entry_content_str, re.IGNORECASE | re.DOTALL)
                        if journal_match:
                            journal_value = journal_match.group(1)
                            
                            # Remove journal field
                            journal_field_pattern = r"journal\s*=\s*[\{\"].*?[\}\"],?"
                            modified_entry_content = re.sub(
                                journal_field_pattern, 
                                "", 
                                current_entry_content_str, 
                                flags=re.IGNORECASE | re.DOTALL
                            )
                            
                            # Check if booktitle already exists
                            if not re.search(r"\bbooktitle\s*=", modified_entry_content, re.IGNORECASE):
                                # Add booktitle field after the entry key
                                key_end_pos = modified_entry_content.find(',') + 1
                                modified_entry_content = (
                                    modified_entry_content[:key_end_pos] + 
                                    f"\n  booktitle = {journal_value}," + 
                                    modified_entry_content[key_end_pos:]
                                )
                            
                            modified_entry = f"@{current_entry_type_str}{{{modified_entry_content}"
                            has_changes = True
            
            # 检查 @article 是否包含 journal
            elif current_entry_type_str.lower() == 'article':
                if not re.search(r"\bjournal\s*=", current_entry_content_str, re.IGNORECASE):
                    issues.append(f"错误: '{entry_key}' (@article) 缺少 'journal' 字段")
                    # Cannot auto-fix this - would need to know what journal to add
                
                if re.search(r"\bbooktitle\s*=", current_entry_content_str, re.IGNORECASE):
                    issues.append(f"警告: '{entry_key}' (@article) 包含 'booktitle' 字段，应该使用 'journal'")
                    
                    if auto_fix:
                        # Find the booktitle field value
                        booktitle_match = re.search(r"booktitle\s*=\s*([\{\"].*?[\}\"])", current_entry_content_str, re.IGNORECASE | re.DOTALL)
                        if booktitle_match:
                            booktitle_value = booktitle_match.group(1)
                            
                            # Remove booktitle field
                            booktitle_field_pattern = r"booktitle\s*=\s*[\{\"].*?[\}\"],?"
                            modified_entry_content = re.sub(
                                booktitle_field_pattern, 
                                "", 
                                current_entry_content_str, 
                                flags=re.IGNORECASE | re.DOTALL
                            )
                            
                            # Check if journal already exists
                            if not re.search(r"\bjournal\s*=", modified_entry_content, re.IGNORECASE):
                                # Add journal field after the entry key
                                key_end_pos = modified_entry_content.find(',') + 1
                                modified_entry_content = (
                                    modified_entry_content[:key_end_pos] + 
                                    f"\n  journal = {booktitle_value}," + 
                                    modified_entry_content[key_end_pos:]
                                )
                            
                            modified_entry = f"@{current_entry_type_str}{{{modified_entry_content}"
                            has_changes = True
            
            if has_changes:
                fixed_entries.append((original_entry, modified_entry, entry_key))
        
        return issues, fixed_entries, content
    
    except Exception as e:
        return [f"处理文件时出错: {str(e)}"], [], None


def generate_diff(original, modified):
    """生成两个文本之间的差异"""
    diff = difflib.unified_diff(
        original.splitlines(),
        modified.splitlines(),
        lineterm=''
    )
    return '\n'.join(diff)


def create_diff_log(fixed_entries, log_file):
    """创建差异日志文件"""
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("# BibTeX修复差异日志\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for i, (original, modified, key) in enumerate(fixed_entries):
            f.write(f"## {i+1}. 条目: {key}\n\n")
            f.write("```diff\n")
            
            diff = generate_diff(original, modified)
            f.write(diff)
            f.write("\n```\n\n")


@click.command()
@click.argument('bib_file', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='显示详细信息')
@click.option('--auto-fix', '-f', is_flag=True, help='自动修复发现的问题并创建新文件')
@click.option('--output-file', '-o', type=click.Path(), help='修复后的输出文件路径，默认为原文件名_fixed.bib')
@click.option('--log-file', '-l', type=click.Path(), help='差异日志文件路径，默认为原文件名_diff_log.md')
def main(bib_file, verbose, auto_fix, output_file, log_file):
    """检查BibTeX文件中的常见问题，并可选择自动修复。
    
    此脚本检查以下内容:
    - @inproceedings条目是否包含booktitle字段 (且不应包含journal字段)。
    - @article条目是否包含journal字段 (且不应包含booktitle字段)。
    - 常见会议和期刊 (如ICLR, CVPR, ICCV, ECCV, NeurIPS, ICML, AAAI, IJCAI, SIGGRAPH, PAMI, IJCV, TIP, TOG等) 
      是否使用了正确的BibTeX类型 (如@inproceedings, @article) 和字段 (如booktitle, journal)，
      并建议使用其全称。
      
    如果使用--auto-fix选项，脚本将尝试修复发现的问题并创建一个新文件。
    """
    click.echo(f"正在检查文件: {bib_file}")
    
    if verbose:
        click.echo("正在寻找以下问题:")
        click.echo("- @inproceedings条目缺少'booktitle'字段或错误地包含'journal'字段")
        click.echo("- @article条目缺少'journal'字段或错误地包含'booktitle'字段")
        click.echo("- ICLR论文是否使用正确的类型(@inproceedings)和字段(booktitle='International Conference on Learning Representations')")
        click.echo("- CVPR论文是否使用正确的类型(@inproceedings)和字段(booktitle='Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition')")
        click.echo("- ICCV论文是否使用正确的类型(@inproceedings)和字段(booktitle='Proceedings of the IEEE/CVF International Conference on Computer Vision')")
        click.echo("- ECCV论文是否使用正确的类型(@inproceedings)和字段(booktitle='Proceedings of the European Conference on Computer Vision')")
        click.echo("- NeurIPS论文是否使用正确的类型(@inproceedings)和字段(booktitle='Advances in Neural Information Processing Systems')")
        click.echo("- ICML论文是否使用正确的类型(@inproceedings)和字段(booktitle='International Conference on Machine Learning')")
        click.echo("- AAAI论文是否使用正确的类型(@inproceedings)和字段(booktitle='Proceedings of the AAAI Conference on Artificial Intelligence')")
        click.echo("- IJCAI论文是否使用正确的类型(@inproceedings)和字段(booktitle='Proceedings of the International Joint Conference on Artificial Intelligence')")
        click.echo("- SIGGRAPH论文是否使用正确的类型(@inproceedings)和字段(booktitle='ACM SIGGRAPH Conference Proceedings')")
        click.echo("- ACMMM会议论文是否使用正确的类型(@inproceedings)和字段(booktitle='Proceedings of the ACM International Conference on Multimedia')")
        click.echo("- MICCAI会议论文是否使用正确的类型(@inproceedings)和字段(booktitle='Medical Image Computing and Computer-Assisted Intervention')")
        click.echo("- PAMI期刊论文是否使用正确的类型(@article)和字段(journal='IEEE Transactions on Pattern Analysis and Machine Intelligence')")
        click.echo("- IJCV期刊论文是否使用正确的类型(@article)和字段(journal='International Journal of Computer Vision')")
        click.echo("- TIP期刊论文是否使用正确的类型(@article)和字段(journal='IEEE Transactions on Image Processing')")
        click.echo("- TOG期刊论文是否使用正确的类型(@article)和字段(journal='ACM Transactions on Graphics')")
        click.echo("- JMLR期刊论文是否使用正确的类型(@article)和字段(journal='Journal of Machine Learning Research')")
        click.echo("- TKDE期刊论文是否使用正确的类型(@article)和字段(journal='IEEE Transactions on Knowledge and Data Engineering')")
        click.echo("- Neurocomputing期刊论文是否使用正确的类型(@article)和字段(journal='Neurocomputing')")
        click.echo("- ACL会议论文是否使用正确的类型(@inproceedings)和字段(booktitle='Proceedings of the Association for Computational Linguistics')")
        
    issues, fixed_entries, original_content = check_and_fix_bib_file(bib_file, auto_fix)
    
    if issues:
        click.echo(click.style(f"\n在 '{bib_file}' 中发现 {len(issues)} 个问题:", fg='yellow'))
        for issue in issues:
            if "错误" in issue:
                click.echo(click.style(f"- {issue}", fg='red'))
            elif "建议" in issue:
                click.echo(click.style(f"- {issue}", fg='blue'))
            else:
                click.echo(click.style(f"- {issue}", fg='yellow'))
    else:
        click.echo(click.style(f"\n'{bib_file}' 检查通过，没有发现问题！", fg='green'))
    
    if auto_fix and fixed_entries:
        # Determine output file path
        if not output_file:
            base_name, ext = os.path.splitext(bib_file)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{base_name}_fixed_{timestamp}{ext}"
        
        # Create a map of original -> modified entries
        replacement_map = {original: modified for original, modified, _ in fixed_entries}
        
        # Re-parse the file and rebuild it with proper formatting
        entry_pattern = r'@(\w+)\s*\{([^@]*?)(?=@|\Z)'
        entries = re.findall(entry_pattern, original_content, re.DOTALL)
        
        # Rebuild the content
        rebuilt_content = ""
        for entry_type, entry_content in entries:
            original_entry = f"@{entry_type}{{{entry_content}"
            
            if original_entry in replacement_map:
                # Get the fixed version
                # import pdb; pdb.set_trace()
                entry_text = replacement_map[original_entry]
                
                # Ensure proper formatting with closing brace on new line
                if entry_text.endswith('}'):
                    # Remove the closing brace and any whitespace before it
                    # entry_text = entry_text.rstrip('}').rstrip()
                    entry_text = entry_text[:-1]
                    # Add closing brace on new line with proper indentation
                    entry_text += "\n}"
            else:
                # Keep the original
                entry_text = original_entry
                
                # Ensure proper formatting with closing brace on new line
                if entry_text.endswith('}'):
                    # Remove the closing brace and any whitespace before it
                    entry_text = entry_text.rstrip('}').rstrip()
                    # Add closing brace on new line
                    entry_text += "\n}"
            
            # Add to rebuilt content with proper spacing
            rebuilt_content += entry_text + "\n\n"
        
        # Remove any extra newlines at the end but ensure at least one
        rebuilt_content = rebuilt_content.rstrip() + "\n"
        
        # Write the rebuilt content
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(rebuilt_content)
        
        click.echo(click.style(f"\n已修复 {len(fixed_entries)} 个条目，保存到: {output_file}", fg='green'))
        
        # Determine log file path and create diff log
        if not log_file:
            base_name, _ = os.path.splitext(output_file)
            log_file = f"{base_name}_diff_log.md"
        
        create_diff_log(fixed_entries, log_file)
        click.echo(click.style(f"差异日志已保存到: {log_file}", fg='green'))
        
        # Display diffs for modified entries
        click.echo(click.style("\n修改前后的差异:", fg='cyan'))
        for original, modified, key in fixed_entries:
            click.echo(click.style(f"\n条目: {key}", fg='cyan'))
            
            # Generate and print diff
            diff = generate_diff(original, modified)
            
            # Color the diff output
            for line in diff.splitlines():
                if line.startswith('+'):
                    click.echo(click.style(line, fg='green'))
                elif line.startswith('-'):
                    click.echo(click.style(line, fg='red'))
                elif line.startswith('@@'):
                    click.echo(click.style(line, fg='cyan'))
                else:
                    click.echo(line)
    elif auto_fix and not fixed_entries:
        click.echo(click.style("\n没有需要修复的条目。", fg='blue'))


if __name__ == "__main__":
    main()
