from unittest import TestCase
from collections import deque

from src.model import Dollars, ExpensesSummary, Expense, ExpensesFromFileSource

class ExpensesSummaryTest(TestCase):
    def testTotalExpenseFromSummaryWithNoSourceIsZeroDollars(self):
        summary = ExpensesSummary.fromSources([])
        totalExpenses = summary.totalExpenses()
        self.assertEqual(totalExpenses,self.zeroDollars())
    
    def testTotalExpenseFromSummaryWithSingleSourceWithNoExpensesIsZeroDollars(self):
        aSource = LoadedExpensesSource()
        summary = ExpensesSummary.fromSources([aSource])
        totalExpenses = summary.totalExpenses()
        self.assertEqual(totalExpenses, self.zeroDollars())
    
    def testTotalExpenseFromSummaryWithSingleSourceWithSingleExpensesIsTenDollars(self):
        tenDollars = self.dollars(10)
        aSource = self.sourceWithSingleExpense(tenDollars)
        summary = ExpensesSummary.fromSources([aSource])
        totalExpenses = summary.totalExpenses()
        self.assertEqual(totalExpenses, tenDollars)
    
    def testTotalExpenseFromSummaryWithSingleSourceWithTwoExpensesIsTwelveDollars(self):
        tenDollars = self.dollars(10)
        twoDollars = self.dollars(2)
        aSource = self.sourceWithExpenses([tenDollars, twoDollars])
        summary = ExpensesSummary.fromSources([aSource])
        totalExpenses = summary.totalExpenses()
        self.assertEqual(totalExpenses, self.dollars(12))
    
    def testTotalExpenseFromSummaryWithTwoSourcesWithSingleExpensesEachIsSeventeenDollars(self):
        eightDollars = self.dollars(8)
        aSource = self.sourceWithSingleExpense(eightDollars)
        nineDollars = self.dollars(9)
        anotherSource = self.sourceWithSingleExpense(nineDollars)
        summary = ExpensesSummary.fromSources([aSource, anotherSource])
        totalExpenses = summary.totalExpenses()
        self.assertEqual(totalExpenses, self.dollars(17))
    
    def testTotalExpenseFromSummaryWithTwoSourcesWithTwoExpensesEachIsTwentyNineDollars(self):
        tenDollars = self.dollars(10)
        twoDollars = self.dollars(2)
        aSource = self.sourceWithExpenses([tenDollars, twoDollars])
        eightDollars = self.dollars(8)
        nineDollars = self.dollars(9)
        anotherSource = self.sourceWithExpenses([nineDollars, eightDollars])
        summary = ExpensesSummary.fromSources([aSource, anotherSource])
        totalExpenses = summary.totalExpenses()
        self.assertEqual(totalExpenses, self.dollars(29))
    
    def testTotalExpenseFromSummaryWithThreeSourcesWithThreeExpensesEachIsThirtyNineDollars(self):
        oneDollar = self.dollars(1)
        twoDollars = self.dollars(2)
        threeDollars = self.dollars(3)
        firstSource = self.sourceWithExpenses([oneDollar, twoDollars, threeDollars])
        fortyDollar = self.dollars(40)
        fiftyDollars = self.dollars(50)
        sixtyDollars = self.dollars(60)
        secondSource = self.sourceWithExpenses([fortyDollar, fiftyDollars, sixtyDollars])
        sevenHundredDollar = self.dollars(700)
        eightHundredDollars = self.dollars(800)
        nineHundredDollars = self.dollars(900)
        thirdSource = self.sourceWithExpenses([sevenHundredDollar, eightHundredDollars, nineHundredDollars])
        summary = ExpensesSummary.fromSources([firstSource, secondSource, thirdSource])
        totalExpenses = summary.totalExpenses()
        self.assertEqual(totalExpenses, self.dollars(2556))

    def zeroDollars(self):
        return Dollars.zero()
    
    def dollars(self,amount):
        return Dollars.amount(amount)
    
    def sourceWithSingleExpense(self, anAmount):
        return self.sourceWithExpenses([anAmount])

    def sourceWithExpenses(self, amounts):
        aSource = LoadedExpensesSource()
        for anAmount in amounts:
            anExpense = Expense.withTotal(anAmount)
            aSource.addExpense(anExpense)
        return aSource


class ExpensesFromFileSourceTest(TestCase):
    def testNoExpensesAreImportedFromEmptyFile(self):
        aFile = TestFile()
        aSource = ExpensesFromFileSource.fromFile(aFile)
        expenses = aSource.expenses()
        self.assertEqual(len(expenses),0)
    
    def testNoIncomesAreImportedFromEmptyFile(self):
        aFile = TestFile()
        aSource = ExpensesFromFileSource.fromFile(aFile)
        incomes = aSource.incomes()
        self.assertEqual(len(incomes),0)
    
    def testSingleExpenseOfTwoDollarsIsImportedFromFile(self):
        aFile = TestFile()
        aFile.addLine('Date,Description,Debit,Credit')
        aFile.addLine('09-27-2024,"PurchaseA",2.00,')
        aSource = ExpensesFromFileSource.fromFile(aFile)
        expenses = aSource.expenses()
        self.assertAllAndOnlyTotalsInDollars(expenses, [2])
    
    def testThreeExpensesOfTwoSixAndTenDollarsAreImportedFromFile(self):
        aFile = TestFile()
        aFile.addLine('Date,Description,Debit,Credit')
        aFile.addLine('09-27-2024,"PurchaseA",2.00,')
        aFile.addLine('09-27-2024,"PurchaseB",6.00,')
        aFile.addLine('09-27-2024,"PurchaseC",10.00,')
        aSource = ExpensesFromFileSource.fromFile(aFile)
        expenses = aSource.expenses()
        self.assertAllAndOnlyTotalsInDollars(expenses, [2, 6, 10])
    
    def testSingleIncomeOfSevenDollarsIsImportedFromFile(self):
        aFile = TestFile()
        aFile.addLine('Date,Description,Debit,Credit')
        aFile.addLine('09-30-2024,"IncomeA",,7.85')
        aSource = ExpensesFromFileSource.fromFile(aFile)
        incomes = aSource.incomes()
        self.assertAllAndOnlyTotalsInDollars(incomes, [7.85])
    
    def testThreeIncomesOfTenTwelveAndTwentyDollarsAreImportedFromFile(self):
        aFile = TestFile()
        aFile.addLine('Date,Description,Debit,Credit')
        aFile.addLine('09-30-2024,"IncomeA",,10.00')
        aFile.addLine('09-30-2024,"IncomeB",,12.00')
        aFile.addLine('09-30-2024,"IncomeC",,20.00')
        aSource = ExpensesFromFileSource.fromFile(aFile)
        incomes = aSource.incomes()
        self.assertAllAndOnlyTotalsInDollars(incomes, [10, 12, 20])
    
    def testTwoIncomesOfTwoAndFourDollarsAndTwoExpensesOfThreeAndFiveAreImportedFromFile(self):
        aFile = TestFile()
        aFile.addLine('Date,Description,Debit,Credit')
        aFile.addLine('09-30-2024,"IncomeA",,2.00')
        aFile.addLine('09-27-2024,"PurchaseA",3.00,')        
        aFile.addLine('09-30-2024,"IncomeB",,4.00')
        aFile.addLine('09-27-2024,"PurchaseB",5.00,')
        aSource = ExpensesFromFileSource.fromFile(aFile)
        expenses = aSource.expenses()
        incomes = aSource.incomes()
        self.assertAllAndOnlyTotalsInDollars(expenses, [3, 5])
        self.assertAllAndOnlyTotalsInDollars(incomes, [2, 4])

    def assertAllAndOnlyTotalsInDollars(self, activities, expectedDollarAmounts):
        self.assertEqual(len(activities), len(activities))
        for activity , expectedDollarAmount in zip(activities, expectedDollarAmounts):
            self.assertEqual(activity.total(), Dollars.amount(expectedDollarAmount))
        

class DollarsTests(TestCase):
    def testEquals(self):
        aZeroDollars = Dollars.zero()
        anotherZeroDollars = Dollars.zero()
        twoDollars = Dollars.amount(2)
        self.assertEqual(aZeroDollars, anotherZeroDollars)
        self.assertNotEqual(aZeroDollars, twoDollars)        
    
    def testHash(self):
        aZeroDollars = Dollars.zero()
        anotherZeroDollars = Dollars.zero()
        twoDollars = Dollars.amount(2)
        self.assertEqual(hash(aZeroDollars), hash(anotherZeroDollars))
        self.assertNotEqual(hash(aZeroDollars), hash(twoDollars))
    
    def testStringRepresentation(self):
        zeroDollars = Dollars.zero()
        self.assertEqual(str(zeroDollars), '0 USD')
        twoDollars = Dollars.amount(2)
        self.assertEqual(str(twoDollars), '2 USD')
    
    def testTwoDollarsPlusFiveDollarsEqualsSevenDollars(self):
        twoDollars = Dollars.amount(2)
        fiveDollars = Dollars.amount(5)
        sevenDollars = Dollars.amount(7)
        self.assertEqual(twoDollars + fiveDollars, sevenDollars)
    

class LoadedExpensesSource():
    def __init__(self):
        self._expenses = []

    def addExpense(self, anExpense):
        self._expenses.append(anExpense)
    
    def expenses(self):
        return self._expenses

class TestFile():
    def __init__(self):
        self._lines = deque()
    
    def addLine(self, aLine):
        self._lines.append(aLine)
    
    def readlines(self):
        readlines = []
        while  self._lines: readlines.append(self.readLine())
        return readlines
    
    def readLine(self):
        return self._lines.popleft()
    
    def __iter__(self):
        iterator = []
        while self._lines: iterator.append(self.readLine())
        return iter(iterator)