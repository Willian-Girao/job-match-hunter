
def from_cv_json_response(json_response) -> str:
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

    try:
        # Technical Skills
        output_as_txt += '[Technical Skills]\n\n'
        # tech skills found within "work experience" category
        for we in work_experience:
            for ts in we['technical_skills']:
                if ts not in technical_skills:
                    technical_skills.append(ts)
        # tech skills found within "education" category
        for ed in education:
            for ts in ed['technical_skills']:
                if ts not in technical_skills:
                    technical_skills.append(ts)
        for ts in technical_skills:
            output_as_txt += f'- {ts}\n'

        # Work Experience
        output_as_txt += '\n[Work Experience]\n'
        for we in work_experience:
            output_as_txt += '\n' + str(we['duration']) + ' months | '
            output_as_txt += we['job_role'].strip().replace("\uFFFD", "") + '\n\n'

            for activity in we['activities']:
                output_as_txt += f'- {activity.strip().replace("\uFFFD", "")}\n'

        # Education
        output_as_txt += '\n[Education]\n'
        for ed in education:
            output_as_txt += '\n' + str(ed['duration']) + ' months | '
            output_as_txt += ed['education_type'].strip().replace("\uFFFD", "") + ' | '
            output_as_txt += ed['field'].strip().replace("\uFFFD", "") + '\n\n'

            for activity in ed['activities']:
                output_as_txt += f'- {activity.strip().replace("\uFFFD", "")}\n'

        # Languages
        output_as_txt += '\n[Languages]\n\n'
        for lg in languages:
            output_as_txt += "- " + lg['language'].strip() + ": " + lg['fluency'].strip() + '\n'
    except Exception as e:
        raise ValueError(f"{type(e).__name__}: {e}")

    return output_as_txt