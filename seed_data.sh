python3 manage.py shell <<'EOF'

from main.models import Experience, Skill, Award
from datetime import date

Experience.objects.all().delete()
Skill.objects.all().delete()
Award.objects.all().delete()

golang = Skill.objects.create(name='Go')
reactjs = Skill.objects.create(name='React.js')
nextjs = Skill.objects.create(name='Next.js')
postgre = Skill.objects.create(name='PostgreSQL')
redis = Skill.objects.create(name='Redis')

pelihara = Experience.objects.create(
    title='Software Engineer Intern',
    company_name='Pelihara',
    company_logo='img/pelihara-logo.webp',
    description='Developed a pet clinic management app.',
    started_at=date(2026, 6, 25),
    ended_at=date(2026, 9, 13),
)

pelihara.skills.add(golang, reactjs, nextjs, postgre, redis)

cpp = Skill.objects.create(name='C++')
algo = Skill.objects.create(name='Algorithms')
da_su = Skill.objects.create(name='Data Structures')
dis_math = Skill.objects.create(name='Discrete Mathematics')
prog_fund = Skill.objects.create(name='Programming Fundamentals')

labschool = Experience.objects.create(
    title='Competitive Programming Tutor',
    company_name='SMA Labschool Ciracas',
    company_logo='img/labschool-ciracas-logo.webp',
    description='Taught foundational programming concepts in C++, from basic syntax to recursion.',
    started_at=date(2026, 6, 13),
    ended_at=date(2026, 6, 13),
)

labschool.skills.add(cpp, prog_fund)

osn = Award.objects.create(
    title='Finalist - OSN Informatika (Indonesian NOI) 2024',
    issuer='Ministry of Education of The Republic of Indonesia',
    description='OSN Informatika is widely regarded as the most prestigious competitive programming competition for high school students in Indonesia. I got ranked 38th among 100 finalists.',
    awarded_at=date(2024, 8, 1),
)

nplc = Award.objects.create(
    title='1st Place - National Programming & Logic Competition 2024',
    issuer='Universitas Ciputra',
    description='National-level competitive programming competition for high school students held by Universitas Ciputra',
    awarded_at=date(2024, 2, 1),
)

exit()
EOF
