
def from_cv_json_response(json_response, schema_name) -> str:
    """
    TODO - type hints
    """
    try:
        technical_skills = json_response['technical_skills']
        work_experience = json_response['work_experience']
        education = json_response['education']
        languages = json_response['languages']
    except Exception as e:
        raise ValueError(f"{type(e).__name__}: {e}")

    output_as_txt = ''

    if schema_name in ['01_cv_parsing.json', '02_cv_parsing.json']:
        try:
            output_as_txt += 'Technical Skills:\n\n'
            for ts in technical_skills:
                output_as_txt += f'{ts.strip().replace("\uFFFD", "")}\n'

            output_as_txt += '\nWork Experience:\n\n'
            for we in work_experience:
                output_as_txt += f'{we.strip().replace("\uFFFD", "")}\n'

            output_as_txt += '\nEducation:\n\n'
            for ed in education:
                output_as_txt += f'{ed.strip().replace("\uFFFD", "")}\n'

            output_as_txt += '\nLanguages:\n\n'
            for lg in languages:
                output_as_txt += f'{lg.strip().replace("\uFFFD", "")}\n'
        except Exception as e:
            raise ValueError(f"{type(e).__name__}: {e}")

    elif schema_name in ['03_cv_parsing.json']:
        try:
            # Technical Skills
            output_as_txt += 'Technical Skills:\n\n'
            # tech skills found within "work experience" category
            for ts in work_experience['technical_skills']:
                if ts not in technical_skills:
                    technical_skills.append(ts)
            # tech skills found within "education" category
            for ts in education['technical_skills']:
                if ts not in technical_skills:
                    technical_skills.append(ts)
            for ts in technical_skills:
                output_as_txt += f'{ts}\n'

            # Work Experience
            output_as_txt += '\nWork Experience:\n\n'
            for we in work_experience:
                output_as_txt += 'duration: ' + we['years'].strip().replace("\uFFFD", "") + ' years\n'
                output_as_txt += 'role: ' + we['role'].strip().replace("\uFFFD", "") + '\n\n'

            # Education
            output_as_txt += '\nEducation:\n\n'
            for ed in education:
                output_as_txt += 'duration: ' + ed['years'].strip().replace("\uFFFD", "") + ' years\n'
                output_as_txt += 'level: ' + ed['level'].strip().replace("\uFFFD", "") + '\n'
                output_as_txt += 'field: ' + ed['field'].strip().replace("\uFFFD", "") + '\n\n'

            # Languages
            output_as_txt += '\nLanguages:\n\n'
            for lg in languages:
                output_as_txt += lg['language'].strip() + ' (' + lg['fluency'].strip() + ')\n'
        except Exception as e:
            raise ValueError(f"{type(e).__name__}: {e}")
    else:
        raise ValueError(f'Argument `schema_name` with value {schema_name} is not valid.')

    return output_as_txt