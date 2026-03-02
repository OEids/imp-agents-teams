"""Generate S2 Data Field Mappings PDF"""
from fpdf import FPDF
from datetime import datetime

class S2MappingsPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'S2 (Strand 2) Data Field Mappings Reference', align='C')
        self.ln(5)
        self.set_draw_color(200, 200, 200)
        self.line(10, 15, 200, 15)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(0, 51, 102)
        self.ln(5)
        self.cell(0, 10, title, ln=True)
        self.set_draw_color(0, 51, 102)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def sub_title(self, title):
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(51, 51, 51)
        self.ln(3)
        self.cell(0, 8, title, ln=True)
        self.ln(1)

    def add_table(self, headers, data, col_widths=None):
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(0, 51, 102)
        self.set_text_color(255, 255, 255)

        if col_widths is None:
            col_widths = [190 / len(headers)] * len(headers)

        # Header row
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 7, header, border=1, fill=True, align='C')
        self.ln()

        # Data rows
        self.set_font('Helvetica', '', 8)
        self.set_text_color(0, 0, 0)
        fill = False
        for row in data:
            if self.get_y() > 265:
                self.add_page()
                self.set_font('Helvetica', 'B', 9)
                self.set_fill_color(0, 51, 102)
                self.set_text_color(255, 255, 255)
                for i, header in enumerate(headers):
                    self.cell(col_widths[i], 7, header, border=1, fill=True, align='C')
                self.ln()
                self.set_font('Helvetica', '', 8)
                self.set_text_color(0, 0, 0)

            self.set_fill_color(245, 245, 245) if fill else self.set_fill_color(255, 255, 255)
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 6, str(cell)[:50], border=1, fill=fill, align='L')
            self.ln()
            fill = not fill
        self.ln(3)

def generate_pdf():
    pdf = S2MappingsPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # Title Page Content
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(0, 51, 102)
    pdf.ln(20)
    pdf.cell(0, 15, 'S2 Data Field Mappings', ln=True, align='C')
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, 'Complete Reference Guide', ln=True, align='C')
    pdf.ln(5)
    pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', ln=True, align='C')
    pdf.ln(20)

    # ========== SECTION 1: Sheet Name Mappings ==========
    pdf.section_title('1. Sheet Name Mappings (Internal to S2 Template)')
    pdf.add_table(
        ['Internal Name', 'S2 Template Sheet'],
        [
            ['PayScales', '19_PayScales'],
            ['PayScalePoints', '20_PayScalePoints'],
            ['PayScaleGrades', '22_PayScaleGrades'],
            ['PayScaleIncreasePercen', '21_PayScaleIncreasePercen'],
            ['AllowanceTypes', '16_AllowanceTypes'],
            ['AllowanceTypePoint', '17_AllowanceTypePoint'],
            ['Pensions', '24_Pensions'],
            ['EQWPatterns', '23_EQWPatterns'],
            ['StfRoleGroup', '26_StfRoleGroup'],
            ['StfRole', '27_StfRole'],
            ['StaffMembers', '25_StaffMembers'],
            ['ContractsTeachFTE', '28_ContractsTeachFTE'],
            ['ContractsSupportHours', '29_ContractsSupportHours'],
            ['ContractAllowances', '34_ContractAllowances'],
            ['ContractAdjustments', '33_ContractAdjustments'],
            ['Finance Codes S2', '11_Finance Codes S2'],
            ['Genders', '12_Genders'],
            ['ContractTypes', '13_ContractTypes'],
            ['LeaveTypes', '30_LeaveTypes'],
            ['AdjustmentTypes', '31_AdjustmentTypes'],
        ],
        [95, 95]
    )

    # ========== SECTION 2: Column Name Mappings ==========
    pdf.add_page()
    pdf.section_title('2. Column Name Mappings (Source to Target)')
    pdf.add_table(
        ['Source Variants', 'Maps To'],
        [
            ['first_name, firstname, forename, given_name, fname', 'first_name'],
            ['last_name, lastname, surname, family_name, lname', 'last_name'],
            ['job_title, jobtitle, position, role_title, post', 'job_title'],
            ['spot_salary, spot scale, spot amount', 'spot_salary'],
            ['annual_salary, salary, annual_pay, gross_salary', 'annual_salary'],
            ['fte, full_time_equivalent, weekly_fte', 'weekly_fte'],
            ['weekly_hours, hours_per_week, contracted_hours', 'weekly_hours'],
            ['full_time_hours, ft_hours, standard_hours', 'full_time_hours'],
            ['scale_point, scalepoint, spine_point, scp', 'current_scale_point'],
            ['pay_scale, payscale, pay_range, salary_scale', 'pay_scale'],
            ['pension, pension_code, pension_scheme', 'pension_code'],
            ['start_date, startdate, commencement, hire_date', 'start_date'],
            ['end_date, enddate, termination, leaving_date', 'end_date'],
            ['contract_type, contracttype, employment_type', 'contract_type'],
            ['equated_weeks, eqw, term_weeks, working_weeks', 'equated_week_pattern'],
            ['payroll, emp_no, employee_number, staff_id', 'payroll_number'],
            ['role_group, staff_role_group, rolegroup', 'staff_role_group'],
            ['gross_salary_fc, salary_finance_code', 'gross_salary_finance_code'],
            ['ni_finance_code, employers_ni_fc', 'employers_ni_finance_code'],
            ['pension_finance_code, pension_fc', 'pension_finance_code'],
        ],
        [120, 70]
    )

    # ========== SECTION 3: Staff Role Group to Finance Codes ==========
    pdf.add_page()
    pdf.section_title('3. Staff Role Group to Finance Codes')
    pdf.add_table(
        ['Role Group', 'Title', 'Gross', 'NI', 'Pension'],
        [
            ['LST', 'Leadership Teaching', '610100', '610200', '610300'],
            ['LSN', 'Leadership Non-Teaching', '625100', '625200', '625300'],
            ['TEA', 'Teachers', '612100', '612200', '612300'],
            ['TA', 'Teaching Assistants', '615100', '615200', '615300'],
            ['ADM', 'Finance and Admin', '625100', '625200', '625300'],
            ['CAT', 'Catering Staff', '2700', '2705', '2710'],
            ['CLE', 'Cleaning Staff', '630100', '630200', '630300'],
            ['PRE', 'Site Staff', '627100', '627200', '627300'],
            ['MDS', 'Midday Supervisors', '635100', '635200', '635300'],
            ['NUR', 'Nursery Staff', '637100', '637200', '637300'],
            ['TEC', 'Technicians', '622100', '622200', '622300'],
            ['LIB', 'Librarians', '620100', '620200', '620300'],
            ['FSW', 'Family Support Workers', '640100', '640200', '640300'],
            ['COV', 'Cover Supervisors', '2720', '2725', '2730'],
            ['COM', 'Community Facilities', '645100', '645200', '645300'],
            ['OTH', 'Other Staff', '650400', '650410', '650420'],
            ['EDS', 'Educational Support', '619100', '619200', '619300'],
        ],
        [25, 55, 35, 35, 35]
    )

    # ========== SECTION 4: Job Title to Role Mappings ==========
    pdf.add_page()
    pdf.section_title('4. Job Title to Role Group Mappings')

    pdf.sub_title('Teaching Leadership')
    pdf.add_table(
        ['Job Title Keywords', 'Role Group', 'Code'],
        [
            ['headteacher, head, principal', 'LST', 'HT'],
            ['executive headteacher, exec head', 'LST', 'EHT'],
            ['deputy headteacher, deputy head', 'LST', 'DHT'],
            ['assistant headteacher, asst head', 'LST', 'AHT'],
        ],
        [100, 45, 45]
    )

    pdf.sub_title('Teachers')
    pdf.add_table(
        ['Job Title Keywords', 'Role Group', 'Code'],
        [
            ['teacher, class teacher, classroom teacher', 'TEA', 'TEA'],
            ['unqualified teacher, trainee teacher', 'TEA', 'UQT'],
            ['upper pay scale, ups teacher', 'TEA', 'TEA_UPS'],
            ['lead practitioner, advanced skills, ast', 'TEA', 'LP'],
        ],
        [100, 45, 45]
    )

    pdf.sub_title('Teaching Assistants')
    pdf.add_table(
        ['Job Title Keywords', 'Role Group', 'Code'],
        [
            ['teaching assistant, ta, classroom assistant', 'TA', 'TA'],
            ['higher level teaching assistant, hlta', 'TA', 'HLTA'],
            ['apprentice ta', 'TA', 'APP_TA'],
        ],
        [100, 45, 45]
    )

    pdf.sub_title('Admin/Finance')
    pdf.add_table(
        ['Job Title Keywords', 'Role Group', 'Code'],
        [
            ['school business manager, sbm', 'ADM', 'SBM'],
            ['office manager, admin manager', 'ADM', 'ADM_MGR'],
            ['admin assistant, administrative assistant', 'ADM', 'ADM_AST'],
            ['finance manager, finance officer, bursar', 'ADM', 'FIN_MGR'],
            ['finance assistant, accounts assistant', 'ADM', 'FIN_AST'],
            ['hr manager, human resources manager', 'ADM', 'HR_MGR'],
            ['hr assistant, human resources assistant', 'ADM', 'HR_AST'],
            ['receptionist, reception, front desk', 'ADM', 'REC'],
        ],
        [100, 45, 45]
    )

    pdf.sub_title('Other Roles')
    pdf.add_table(
        ['Job Title Keywords', 'Role Group', 'Code'],
        [
            ['site manager, premises manager, facilities', 'PRE', 'SITE_MGR'],
            ['caretaker, janitor', 'PRE', 'CT'],
            ['catering manager, kitchen manager, chef', 'CAT', 'CAT_MGR'],
            ['catering assistant, kitchen assistant, cook', 'CAT', 'CAT_AST'],
            ['cleaner, cleaning staff, domestic', 'CLE', 'CLE'],
            ['midday supervisor, lunchtime supervisor', 'MDS', 'MDS'],
            ['nursery manager', 'NUR', 'NUR_MGR'],
            ['nursery nurse, early years practitioner', 'NUR', 'NUR_NUR'],
            ['technician, ict technician, science tech', 'TEC', 'TEC'],
            ['librarian, library assistant', 'LIB', 'LIB'],
            ['family support worker, family liaison', 'FSW', 'FSW'],
            ['cover supervisor', 'COV', 'COV_SUP'],
        ],
        [100, 45, 45]
    )

    # ========== SECTION 5: Pay Scale Mappings by Location ==========
    pdf.add_page()
    pdf.section_title('5. Role Group to Pay Scale (by Location)')

    pdf.sub_title('Teaching Roles')
    pdf.add_table(
        ['Role Group', 'EW', 'FRI', 'IL', 'OL'],
        [
            ['LST (Leadership)', 'LS_EW', 'LS_FRI', 'LS_IL', 'LS_OL'],
            ['TEA (Teachers)', 'MAIN_EW', 'MAIN_FRI', 'MAIN_IL', 'MAIN_OL'],
        ],
        [50, 35, 35, 35, 35]
    )

    pdf.sub_title('Support Roles')
    pdf.add_table(
        ['Role Group', 'EW', 'FRI', 'IL', 'OL', 'KEN'],
        [
            ['ADM', 'NJC_EW', 'NJC_FRI', 'NJC_IL', 'NJC_OL', 'KENT'],
            ['TA', 'NJC_EW', 'NJC_FRI', 'NJC_IL', 'NJC_OL', 'KENT'],
            ['CAT', 'NJC_EW', 'NJC_FRI', 'NJC_IL', 'NJC_OL', 'KENT'],
            ['CLE', 'NJC_EW', 'NJC_FRI', 'NJC_IL', 'NJC_OL', 'KENT'],
            ['PRE', 'NJC_EW', 'NJC_FRI', 'NJC_IL', 'NJC_OL', 'KENT'],
            ['MDS', 'NJC_EW', 'NJC_FRI', 'NJC_IL', 'NJC_OL', 'KENT'],
            ['NUR', 'NJC_EW', 'NJC_FRI', 'NJC_IL', 'NJC_OL', 'KENT'],
            ['TEC', 'NJC_EW', 'NJC_FRI', 'NJC_IL', 'NJC_OL', 'KENT'],
            ['LIB', 'NJC_EW', 'NJC_FRI', 'NJC_IL', 'NJC_OL', 'KENT'],
            ['FSW', 'NJC_EW', 'NJC_FRI', 'NJC_IL', 'NJC_OL', 'KENT'],
            ['COV', 'NJC_EW', 'NJC_FRI', 'NJC_IL', 'NJC_OL', 'KENT'],
            ['OTH', 'NJC_EW', 'NJC_FRI', 'NJC_IL', 'NJC_OL', 'KENT'],
        ],
        [30, 32, 32, 32, 32, 32]
    )

    # ========== SECTION 6: Department Code Mappings ==========
    pdf.add_page()
    pdf.section_title('6. Role Group to Department Code')
    pdf.add_table(
        ['Role Group', 'Department Code'],
        [
            ['LST (Leadership Teaching)', 'SAL_LST'],
            ['LSN (Leadership Non-Teaching)', 'SAL_LST'],
            ['TEA (Teachers)', 'SAL_TEA'],
            ['TA (Teaching Assistants)', 'SAL_TA'],
            ['ADM (Admin)', 'SAL_ADM'],
            ['CAT (Catering)', 'SAL_CAT'],
            ['CLE (Cleaning)', 'SAL_CLE'],
            ['PRE (Premises)', 'SAL_PRE'],
            ['MDS (Midday)', 'SAL_MDS'],
            ['NUR (Nursery)', 'SAL_NUR'],
            ['TEC (Technicians)', 'SAL_TEC'],
            ['LIB (Library)', 'SAL_LIB'],
            ['FSW (Family Support)', 'SAL_FSW'],
            ['COV (Cover)', 'SAL_COV'],
            ['COM (Community)', 'SAL_COM'],
            ['OTH (Other)', 'SAL_OTH'],
            ['ESTF (External)', 'SAL_EXT'],
        ],
        [95, 95]
    )

    # ========== SECTION 7: Location and Working Hours ==========
    pdf.section_title('7. Location Variants and Default Working Hours')
    pdf.add_table(
        ['Code', 'Location Name', 'Teaching Hrs', 'Support Hrs', 'Pay Scale Suffix'],
        [
            ['EW', 'England & Wales', '32.5', '37.0', '_EW'],
            ['FRI', 'Fringe', '32.43', '37.0', '_FRI'],
            ['IL', 'Inner London', '25.0', '36.0', '_IL'],
            ['OL', 'Outer London', '27.5', '37.5', '_OL'],
            ['KEN', 'Kent', '32.5', '37.0', '_KEN'],
            ['NMW', 'National Minimum Wage', '37.0', '37.0', '_NMW'],
        ],
        [25, 55, 35, 35, 40]
    )

    # ========== SECTION 8: Pension Scheme Mappings ==========
    pdf.add_page()
    pdf.section_title('8. Pension Scheme Mappings')
    pdf.add_table(
        ['Code', 'Title', 'Employer %', 'For Roles'],
        [
            ['TPS', 'Teachers Pensions Scheme', '23.6%', 'Teaching Staff'],
            ['LGPS_IMP', 'LGPS IMP', '~20%', 'Support Staff'],
            ['LGPS_BNT', 'LGPS Barnett', 'Varies', 'Support Staff'],
            ['LGPS_KEN', 'LGPS Kent', 'Varies', 'Support Staff'],
            ['LGPS_LNS', 'LGPS Lincolnshire', 'Varies', 'Support Staff'],
            ['OPTOUT', 'Opted Out', '0%', 'Any'],
            ['0%', 'No Pension', '0%', 'Any'],
        ],
        [40, 60, 40, 50]
    )

    # ========== SECTION 9: Contract Type Codes ==========
    pdf.section_title('9. Contract Type Codes')
    pdf.add_table(
        ['Code', 'Title', 'Description'],
        [
            ['PERM', 'Permanent', 'Ongoing permanent contract'],
            ['FXT', 'Fixed Term', 'Contract with defined end date'],
            ['MAT', 'Maternity Cover', 'Covering maternity leave'],
            ['ZZZ', 'Standard/Not Selected', 'Default permanent contract'],
        ],
        [40, 60, 90]
    )

    # ========== SECTION 10: Equated Week Patterns ==========
    pdf.section_title('10. Equated Week Patterns')
    pdf.add_table(
        ['Code', 'Title', 'FT Weeks', 'Typical Usage'],
        [
            ['39WEEKSWORKED', '39 weeks worked', '52.143', 'Teachers (term-time)'],
            ['TEA_ALLYEAR', 'Teaching Staff All Year', '52.14', 'Teachers/Leadership'],
            ['SUPALLYEAR', 'Support Staff All Year', '52.14', 'Support/Admin'],
            ['SUPTTO', 'Support TTO', '52.14', 'Support/TAs'],
            ['SUPTTO+1', 'Support TTO Plus 1', '52.14', 'Support'],
            ['SUPTTO+2', 'Support TTO Plus 2', '52.14', 'Support'],
            ['MONTHLYADJUSTMENT', 'Monthly Adjustment', '3.2439', 'Adjustments'],
        ],
        [50, 55, 30, 55]
    )

    # ========== SECTION 11: Combined Column Parsing ==========
    pdf.add_page()
    pdf.section_title('11. Combined Column Parsing Rules')
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 5, 'These columns use "CODE: Title" format and are parsed into separate code/title fields.')
    pdf.ln(3)
    pdf.add_table(
        ['Source Combined Column', 'Code Output', 'Title Output'],
        [
            ['Staff Member Combined', 'StaffMemberCode', 'StaffMemberName'],
            ['Staff Role Combined', 'StaffRoleCode', 'StaffRoleTitle'],
            ['Contract Type Combined', 'ContractTypeCode', 'ContractTypeTitle'],
            ['Pay Scale Combined', 'PayScaleCode', 'PayScaleTitle'],
            ['Pay Scale Grade Combined', 'PayScaleGradeCode', 'PayScaleGradeTitle'],
            ['Pay Scale Point Combined', 'PayScalePointCode', 'PayScalePointTitle'],
            ['Pension Combined', 'PensionCode', 'PensionTitle'],
            ['Equated Week Pattern Combined', 'EquatedWeekPatternCode', 'EquatedWeekPatternTitle'],
            ['Department Combined', 'DepartmentCode', 'DepartmentTitle'],
            ['Fund Combined', 'FundCode', 'FundTitle'],
            ['School Combined', 'SchoolCode', 'SchoolName'],
            ['Gender Combined', 'GenderCode', 'GenderTitle'],
        ],
        [70, 60, 60]
    )

    # ========== SECTION 12: FTE Finance Codes ==========
    pdf.section_title('12. FTE Finance Codes by Role Group')
    pdf.add_table(
        ['Role Group', 'Weekly FTE Code', 'Annual FTE Code'],
        [
            ['LST', 'WK_FTE_LST', 'A_FTE_LST'],
            ['LSN', 'WK_FTE_LSN', 'A_FTE_LSN'],
            ['TEA', 'WK_FTE_TEA', 'A_FTE_TEA'],
            ['TA', 'WK_FTE_TA', 'A_FTE_TA'],
            ['ADM', 'WK_FTE_ADM', 'A_FTE_ADM'],
            ['CLE', 'WK_FTE_CLE', 'A_FTE_CLE'],
            ['PRE', 'WK_FTE_PRE', 'A_FTE_PRE'],
            ['MDS', 'WK_FTE_MDS', 'A_FTE_MDS'],
            ['NUR', 'WK_FTE_NUR', 'A_FTE_NUR'],
            ['TEC', 'WK_FTE_TEC', 'A_FTE_TEC'],
        ],
        [60, 65, 65]
    )

    # ========== SECTION 13: Staff Role Groups Reference ==========
    pdf.add_page()
    pdf.section_title('13. All 59 Staff Role Groups')

    pdf.sub_title('Teaching (3 groups)')
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, 'TEA (Teachers), LST (Leadership Teaching), SLT (Senior Leadership)')
    pdf.ln(3)

    pdf.sub_title('Support Roles (56 groups)')
    pdf.set_font('Helvetica', '', 8)
    pdf.multi_cell(0, 5,
        'ADM, APP, ASC, BFC, BRD_DIR, BRD_IND, CAT, CEN, CLE, COM, COV, CT, CUR, DEV, DRI, '
        'EDS, EST, EXA, EXT, FIN, FLA, FSW, GOV, HLTA, HR, INC, INV, IT, LIB, LM, LTS, MDS, '
        'NUR, OTH, OTH_DIR, OUT, PAS, PERI, PRE, PS, SC, SCITT, SLT, SPO, SSUP, STA, '
        'STEA_LT, STEA_ST, TA, TEC, WEL'
    )

    # ========== SECTION 14: Validation Rules ==========
    pdf.add_page()
    pdf.section_title('14. Data Validation Rules')

    pdf.sub_title('Date Formats')
    pdf.add_table(
        ['Format Type', 'Format', 'Example'],
        [
            ['Full dates', 'YYYY-MM-DD (ISO)', '2024-09-01'],
            ['Partial dates', 'MM/DD', '01/04'],
            ['Financial years', 'YYYY/YY', '2024/25'],
            ['UK display', 'dd/mm/yy', '01/09/24'],
        ],
        [60, 65, 65]
    )

    pdf.sub_title('Boolean Values')
    pdf.add_table(
        ['Valid Values', 'Invalid Values'],
        [
            ['True, False', 'true, false, TRUE, FALSE'],
            ['', 'Yes, No, 1, 0'],
        ],
        [95, 95]
    )

    pdf.sub_title('Numeric Precision')
    pdf.add_table(
        ['Data Type', 'Decimal Places', 'Examples'],
        [
            ['FTE', '1', '0.2, 0.4, 0.5, 1.0'],
            ['Hours per week', '1-2', '37.0, 37.5, 32.43'],
            ['Full-time weeks', '3', '52.143, 52.1429'],
            ['Pay rate', '2', '50025.00, 478.51'],
            ['Percentage', '0-2', '0, 3, 1.75, 2.25'],
            ['Scale point', 'Integer', '1, 2, 3, 18, 43'],
        ],
        [60, 50, 80]
    )

    pdf.sub_title('Value Ranges')
    pdf.add_table(
        ['Field', 'Minimum', 'Maximum'],
        [
            ['WeeklyFteOrHpw (FTE)', '0.0', '1.0'],
            ['FullTimeHoursPerWeek', '0.0', '50.0'],
            ['ScalePointNumber', '1', '100'],
            ['ServiceYears', '0', '99'],
            ['Percentage fields', '0', '100'],
        ],
        [70, 60, 60]
    )

    pdf.sub_title('Empty Value Handling')
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5,
        "Use empty string ('') for missing values.\n"
        "NOT: nan, NaN, None, null, N/A, #N/A\n"
        "DateTo can be empty for ongoing contracts.\n"
        "ScenarioCode typically empty (global scenario)."
    )

    # ========== SECTION 15: Fund Codes ==========
    pdf.add_page()
    pdf.section_title('15. Fund Codes')
    pdf.add_table(
        ['Code', 'Title', 'Description'],
        [
            ['GAG', 'General Annual Grant', 'Main school funding (default)'],
            ['PP', 'Pupil Premium', 'Additional funding for disadvantaged'],
            ['PE', 'PE & Sports Premium', 'Sports and physical education'],
            ['UIFSM', 'Universal Infant Free School Meals', 'Free meals funding'],
            ['SCA', 'School Condition Allocation', 'Building maintenance'],
            ['DFC', 'Devolved Formula Capital', 'Capital funding'],
        ],
        [30, 70, 90]
    )

    # ========== SECTION 16: Teacher Pay Points ==========
    pdf.section_title('16. Teacher Pay Points (2024-25)')

    pdf.sub_title('Main Pay Scale (M1-M6)')
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(0, 6, 'M1: 31,650 | M2: 33,483 | M3: 35,674 | M4: 37,895 | M5: 40,377 | M6: 43,607', ln=True)

    pdf.sub_title('Upper Pay Scale (U1-U3)')
    pdf.cell(0, 6, 'U1: 45,646 | U2: 47,340 | U3: 49,084', ln=True)

    pdf.sub_title('Unqualified (UQ1-UQ6)')
    pdf.cell(0, 6, 'UQ1: 22,637 | UQ2: 24,781 | UQ3: 26,878 | UQ4: 28,969 | UQ5: 31,077 | UQ6: 33,455', ln=True)

    pdf.sub_title('Leadership Scale')
    pdf.cell(0, 6, 'L01: 47,185 ... L43: 128,443 (43 points)', ln=True)

    # Save
    output_path = 'reports/S2_Data_Field_Mappings.pdf'
    pdf.output(output_path)
    return output_path

if __name__ == '__main__':
    output = generate_pdf()
    print(f"PDF generated: {output}")
