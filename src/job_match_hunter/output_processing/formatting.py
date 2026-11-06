
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
        output_as_txt += '\n[Professional Experience]\n'
        for we in work_experience:
            if we['job_role'] or we['activities']:
                output_as_txt += ('\n' + str(we['duration']) + ' months | ') if we['duration'] else '\nunknown months | '
                output_as_txt += str(we['job_role']).strip().replace("\uFFFD", "") + '\n\n'

                for activity in we['activities']:
                    output_as_txt += f'- {activity.strip().replace("\uFFFD", "")}\n'

        # Education
        output_as_txt += '\n[Education]\n'
        for ed in education:
            if ed['education_type'] or ed['activities']:
                output_as_txt += ('\n' + str(ed['duration']) + ' months | ') if ed['duration'] else '\nunknown months | '
                output_as_txt += str(ed['education_type']).strip().replace("\uFFFD", "") + ' | '
                output_as_txt += str(ed['field']).strip().replace("\uFFFD", "") + '\n\n'

                for activity in ed['activities']:
                    output_as_txt += f'- {activity.strip().replace("\uFFFD", "")}\n'

        # Languages
        output_as_txt += '\n[Languages]\n\n'
        for lg in languages:
            output_as_txt += "- " + lg['language'].strip() + ": " + lg['fluency'].strip() + '\n'
    except Exception as e:
        raise ValueError(f"{type(e).__name__}: {e}")

    return output_as_txt

def from_jd_json_response(json_response) -> str:
    """
    TODO - type hints
    """
    try:
        technical_skills = json_response['technical_skills']
        professional_experience = json_response['professional_experience']
        education = json_response['education']
        languages = json_response['languages']
        hard_requirements = json_response['hard_requirements']
        soft_requirements = json_response['soft_requirements']
    except Exception as e:
        raise ValueError(f"{type(e).__name__}: {e}")

    output_as_txt = ''

    try:
        # Technical Skills
        output_as_txt += '[Technical Skills]\n\n'
        # tech skills found within "work experience" category
        for we in professional_experience:
            for ts in we['technical_skills']:
                if ts not in technical_skills:
                    technical_skills.append(ts)

        for ts in technical_skills:
            output_as_txt += f'- {ts}\n'

        # Work Experience
        output_as_txt += '\n[Professional Experience]\n'
        for we in professional_experience:
            if we['job_role'] or we['activities']:
                output_as_txt += ('\n' + str(we['duration']) + ' months | ') if we['duration'] else '\nunknown months | '
                output_as_txt += str(we['job_role']).strip().replace("\uFFFD", "") + '\n\n'

                for activity in we['activities']:
                    output_as_txt += f'- {activity.strip().replace("\uFFFD", "")}\n'

        # Education
        output_as_txt += '\n[Education]\n'
        for ed in education:
            if ed['education_type']:
                output_as_txt += '\n' + str(ed['education_type']).strip().replace("\uFFFD", "") + ' | '
                output_as_txt += str(ed['field']).strip().replace("\uFFFD", "") if ed['field'] else "unspecified"
                output_as_txt += '\n\n'

        # Languages
        output_as_txt += '\n[Languages]\n\n'
        for lg in languages:
            output_as_txt += "- " + lg['language'].strip()
            output_as_txt += (": " + lg['fluency'].strip() + '\n') if lg['fluency'] else '\n'

        # Hard Requirements
        output_as_txt += '\n[Hard Requirements]\n\n'
        for hd in hard_requirements:
            output_as_txt += "- " + hd.strip() + '\n'

        # Soft Requirements
        output_as_txt += '\n[Soft Requirements]\n\n'
        for sr in soft_requirements:
            output_as_txt += "- " + sr.strip() + '\n'
    except Exception as e:
        raise ValueError(f"{type(e).__name__}: {e}")

    return output_as_txt