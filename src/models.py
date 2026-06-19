from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InsuranceBreakdown:
    """Annual social insurance amounts split between employee and employer."""

    health_employee: int
    health_employer: int
    care_employee: int
    care_employer: int
    pension_employee: int
    pension_employer: int
    employment_employee: int
    employment_employer: int
    child_care_contribution_employer: int
    health_standard_monthly: int
    pension_standard_monthly: int

    @property
    def employee_total(self) -> int:
        return (
            self.health_employee
            + self.care_employee
            + self.pension_employee
            + self.employment_employee
        )

    @property
    def employer_total(self) -> int:
        return (
            self.health_employer
            + self.care_employer
            + self.pension_employer
            + self.employment_employer
            + self.child_care_contribution_employer
        )


@dataclass(frozen=True)
class TaxBreakdown:
    """Annual tax amounts."""

    income_tax: int
    resident_tax: int
    taxable_income_for_income_tax: int
    taxable_income_for_resident_tax: int

    @property
    def total(self) -> int:
        return self.income_tax + self.resident_tax


@dataclass(frozen=True)
class SimulationResult:
    """One annual salary simulation result."""

    annual_salary: int
    monthly_salary: int
    salary_income_deduction: int
    salary_income: int
    insurance: InsuranceBreakdown
    tax: TaxBreakdown
    annual_take_home: int
    monthly_take_home_average: int
    total_labor_cost: int
    provisional: bool
    notice: str
