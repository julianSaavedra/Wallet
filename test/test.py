from unittest import TestCase
from collections import deque

from src.model import Dollars, ExpensesAndIncomeSummary, Expense, Income, ExpensesAndIncomesFromFileSource, StatementActivityLineParser

class ExpensesAndIncomeSummaryTest(TestCase):
    def testTotalExpenseFromSummaryWithNoSourceIsZeroDollars(self):
        summary = ExpensesAndIncomeSummary.fromSources([])
        totalExpenses = summary.totalExpenses()
        self.assertEqual(totalExpenses,self.zeroDollars())
    
    def testTotalExpenseFromSummaryWithSingleSourceWithNoExpensesIsZeroDollars(self):
        aSource = LoadedExpensesAndIncomesSource()
        summary = ExpensesAndIncomeSummary.fromSources([aSource])
        totalExpenses = summary.totalExpenses()
        self.assertEqual(totalExpenses, self.zeroDollars())
    
    def testTotalExpenseFromSummaryWithSingleSourceWithSingleExpensesIsTenDollars(self):
        tenDollars = self.dollars(10)
        aSource = self.sourceWithSingleExpense(tenDollars)
        summary = ExpensesAndIncomeSummary.fromSources([aSource])
        totalExpenses = summary.totalExpenses()
        self.assertEqual(totalExpenses, tenDollars)
    
    def testTotalExpenseFromSummaryWithSingleSourceWithTwoExpensesIsTwelveDollars(self):
        tenDollars = self.dollars(10)
        twoDollars = self.dollars(2)
        aSource = self.sourceWithExpenses([tenDollars, twoDollars])
        summary = ExpensesAndIncomeSummary.fromSources([aSource])
        totalExpenses = summary.totalExpenses()
        self.assertEqual(totalExpenses, self.dollars(12))
    
    def testTotalExpenseFromSummaryWithTwoSourcesWithSingleExpensesEachIsSeventeenDollars(self):
        eightDollars = self.dollars(8)
        aSource = self.sourceWithSingleExpense(eightDollars)
        nineDollars = self.dollars(9)
        anotherSource = self.sourceWithSingleExpense(nineDollars)
        summary = ExpensesAndIncomeSummary.fromSources([aSource, anotherSource])
        totalExpenses = summary.totalExpenses()
        self.assertEqual(totalExpenses, self.dollars(17))
    
    def testTotalExpenseFromSummaryWithTwoSourcesWithTwoExpensesEachIsTwentyNineDollars(self):
        tenDollars = self.dollars(10)
        twoDollars = self.dollars(2)
        aSource = self.sourceWithExpenses([tenDollars, twoDollars])
        eightDollars = self.dollars(8)
        nineDollars = self.dollars(9)
        anotherSource = self.sourceWithExpenses([nineDollars, eightDollars])
        summary = ExpensesAndIncomeSummary.fromSources([aSource, anotherSource])
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
        summary = ExpensesAndIncomeSummary.fromSources([firstSource, secondSource, thirdSource])
        totalExpenses = summary.totalExpenses()
        self.assertEqual(totalExpenses, self.dollars(2556))

    def testTotalIncomeFromSummaryWithNoSourceIsZeroDollars(self):
        summary = ExpensesAndIncomeSummary.fromSources([])
        totalIncome = summary.totalIncome()
        self.assertEqual(totalIncome,self.zeroDollars())

    def testTotalIncomeFromSummaryWithSingleSourceWithNoIncomesIsZeroDollars(self):
        aSource = LoadedExpensesAndIncomesSource()
        summary = ExpensesAndIncomeSummary.fromSources([aSource])
        totalIncome = summary.totalIncome()
        self.assertEqual(totalIncome, self.zeroDollars())

    def testTotalIncomeFromSummaryWithSingleSourceWithSingleIncomeIsFiftyDollars(self):
        fiftyDollars = self.dollars(50)
        aSource = self.sourceWithSingleIncome(fiftyDollars)
        summary = ExpensesAndIncomeSummary.fromSources([aSource])
        totalIncome = summary.totalIncome()
        self.assertEqual(totalIncome, fiftyDollars)

    def testTotalIncomeFromSummaryWithThreeSourcesWithThreeIncomesEachIsThirtyNineDollars(self):
        oneDollar = self.dollars(1)
        twoDollars = self.dollars(2)
        threeDollars = self.dollars(3)
        firstSource = self.sourceWithIncomes([oneDollar, twoDollars, threeDollars])
        fortyDollar = self.dollars(40)
        fiftyDollars = self.dollars(50)
        sixtyDollars = self.dollars(60)
        secondSource = self.sourceWithIncomes([fortyDollar, fiftyDollars, sixtyDollars])
        sevenHundredDollar = self.dollars(700)
        eightHundredDollars = self.dollars(800)
        nineHundredDollars = self.dollars(900)
        thirdSource = self.sourceWithIncomes([sevenHundredDollar, eightHundredDollars, nineHundredDollars])
        summary = ExpensesAndIncomeSummary.fromSources([firstSource, secondSource, thirdSource])
        totalIncome = summary.totalIncome()
        self.assertEqual(totalIncome, self.dollars(2556))

    def zeroDollars(self):
        return Dollars.zero()
    
    def dollars(self,amount):
        return Dollars.amount(amount)
    
    def sourceWithSingleExpense(self, anAmount):
        return self.sourceWithExpenses([anAmount])
    
    def sourceWithSingleIncome(self, anAmount):
        return self.sourceWithIncomes([anAmount])

    def sourceWithExpenses(self, amounts):
        aSource = LoadedExpensesAndIncomesSource()
        for anAmount in amounts:
            anExpense = Expense.withTotal(anAmount)
            aSource.addExpense(anExpense)
        return aSource
    
    def sourceWithIncomes(self, amounts):
        aSource = LoadedExpensesAndIncomesSource()
        for anAmount in amounts:
            anExpense = Income.withTotal(anAmount)
            aSource.addIncome(anExpense)
        return aSource


class ExpensesAndIncomesFromFileSourceTest(TestCase):
    def testNoExpensesAreImportedFromEmptyFile(self):
        aFile = TestFile()
        parser = StatementActivityLineParser.commaSeparatedValues()
        aSource = ExpensesAndIncomesFromFileSource.fromFile(aFile, parser)
        expenses = aSource.expenses()
        self.assertEqual(len(expenses),0)
    
    def testNoIncomesAreImportedFromEmptyFile(self):
        aFile = TestFile()
        parser = StatementActivityLineParser.commaSeparatedValues()
        aSource = ExpensesAndIncomesFromFileSource.fromFile(aFile, parser)
        incomes = aSource.incomes()
        self.assertEqual(len(incomes),0)
    
    def testSingleExpenseOfTwoDollarsIsImportedFromFile(self):
        aFile = TestFile()
        aFile.addLine('Date,Description,Debit,Credit\n')
        aFile.addLine('09-27-2024,"PurchaseA",2.00,\n')
        parser = StatementActivityLineParser.commaSeparatedValues()
        aSource = ExpensesAndIncomesFromFileSource.fromFile(aFile, parser)
        expenses = aSource.expenses()
        self.assertAllAndOnlyTotalsInDollars(expenses, [2])
    
    def testThreeExpensesOfTwoSixAndTenDollarsAreImportedFromFile(self):
        aFile = TestFile()
        aFile.addLine('Date,Description,Debit,Credit')
        aFile.addLine('09-27-2024,"PurchaseA",2.00,')
        aFile.addLine('09-27-2024,"PurchaseB",6.00,')
        aFile.addLine('09-27-2024,"PurchaseC",10.00,')
        parser = StatementActivityLineParser.commaSeparatedValues()
        aSource = ExpensesAndIncomesFromFileSource.fromFile(aFile, parser)
        expenses = aSource.expenses()
        self.assertAllAndOnlyTotalsInDollars(expenses, [2, 6, 10])
    
    def testSingleIncomeOfSevenDollarsIsImportedFromFile(self):
        aFile = TestFile()
        aFile.addLine('Date,Description,Debit,Credit')
        aFile.addLine('09-30-2024,"IncomeA",,7.85')
        parser = StatementActivityLineParser.commaSeparatedValues()
        aSource = ExpensesAndIncomesFromFileSource.fromFile(aFile, parser)
        incomes = aSource.incomes()
        self.assertAllAndOnlyTotalsInDollars(incomes, [7.85])
    
    def testThreeIncomesOfTenTwelveAndTwentyDollarsAreImportedFromFile(self):
        aFile = TestFile()
        aFile.addLine('Date,Description,Debit,Credit')
        aFile.addLine('09-30-2024,"IncomeA",,10.00')
        aFile.addLine('09-30-2024,"IncomeB",,12.00')
        aFile.addLine('09-30-2024,"IncomeC",,20.00')
        parser = StatementActivityLineParser.commaSeparatedValues()
        aSource = ExpensesAndIncomesFromFileSource.fromFile(aFile, parser)
        incomes = aSource.incomes()
        self.assertAllAndOnlyTotalsInDollars(incomes, [10, 12, 20])
    
    def testTwoIncomesOfTwoAndFourDollarsAndTwoExpensesOfThreeAndFiveAreImportedFromFile(self):
        aFile = TestFile()
        aFile.addLine('Date,Description,Debit,Credit')
        aFile.addLine('09-30-2024,"IncomeA",,2.00')
        aFile.addLine('09-27-2024,"PurchaseA",3.00,')        
        aFile.addLine('09-30-2024,"IncomeB",,4.00')
        aFile.addLine('09-27-2024,"PurchaseB",5.00,')
        parser = StatementActivityLineParser.commaSeparatedValues()
        aSource = ExpensesAndIncomesFromFileSource.fromFile(aFile, parser)
        expenses = aSource.expenses()
        incomes = aSource.incomes()
        self.assertAllAndOnlyTotalsInDollars(expenses, [3, 5])
        self.assertAllAndOnlyTotalsInDollars(incomes, [2, 4])

    def assertAllAndOnlyTotalsInDollars(self, activities, expectedDollarAmounts):
        self.assertEqual(len(activities), len(activities))
        for activity , expectedDollarAmount in zip(activities, expectedDollarAmounts):
            self.assertEqual(activity.total(), Dollars.amount(expectedDollarAmount))
        

class StatementActivityLineParserTest(TestCase):
    def testLineWithFourCommaSeparatedValuesIsParsedIntoAListWithThoseFourValues(self):
        parser = StatementActivityLineParser.commaSeparatedValues()
        parsedLine = parser.parse('A,$,Hello,1.0')
        self.assertEqual(parsedLine, ['A', '$', 'Hello', '1.0'])

    def testLineWithNoValueAfterTheFirstCommaIsParsedIntoAListWithAnEmptyStringsInSecondPlace(self):
        parser = StatementActivityLineParser.commaSeparatedValues()
        parsedLine = parser.parse('A,,Hello,1.0')
        self.assertEqual(parsedLine, ['A', '', 'Hello', '1.0'])

    def testLineWithNoValueAfterLastCommaIsParsedIntoAListWithAnEmptyStringAtTheEnd(self):
        parser = StatementActivityLineParser.commaSeparatedValues()
        parsedLine = parser.parse('A,$,Hello,')
        self.assertEqual(parsedLine, ['A', '$', 'Hello', ''])
    
    def testLineWithNoValueBeforeFirstCommaIsParsedIntoAListWithAnEmptyStringAtTheFirstPlace(self):
        parser = StatementActivityLineParser.commaSeparatedValues()
        parsedLine = parser.parse(',$,Hello,1.0')
        self.assertEqual(parsedLine, ['', '$', 'Hello', '1.0'])
    
    def testWhiteSpacesAtTheStartOrEndOfCommaSeparatedValuesAreIgnored(self):
        parser = StatementActivityLineParser.commaSeparatedValues()
        parsedLine = parser.parse('A,$ , Hello World,1.0\n')
        self.assertEqual(parsedLine, ['A', '$', 'Hello World', '1.0'])
    
    def testLinesSectionWithCommaWithinQuotesIsParsedAsASingleValue(self):
        parser = StatementActivityLineParser.commaSeparatedValues(boundingCharacter='"')
        parsedLine = parser.parse('123,"NY,USA",456')
        self.assertEqual(parsedLine, ['123', 'NY,USA', '456'])
    


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
        self.assertEqual(str(zeroDollars), '0.00 USD')
        twoDollars = Dollars.amount(2)
        self.assertEqual(str(twoDollars), '2.00 USD')
        oneDollarAndAThird = Dollars.amount(1 + 1/3)
        self.assertEqual(str(oneDollarAndAThird), '1.33 USD')
    
    def testTwoDollarsPlusFiveDollarsEqualsSevenDollars(self):
        twoDollars = Dollars.amount(2)
        fiveDollars = Dollars.amount(5)
        sevenDollars = Dollars.amount(7)
        self.assertEqual(twoDollars + fiveDollars, sevenDollars)
    
    def testTwentyDollarsMinusFourteenDollarsEqualsSixDollars(self):
        twentyDollars = Dollars.amount(20)
        fourteenDollars = Dollars.amount(14)
        sixDollars = Dollars.amount(6)
        self.assertEqual(twentyDollars - fourteenDollars, sixDollars)
    

class LoadedExpensesAndIncomesSource():
    def __init__(self):
        self._expenses = []
        self._incomes = []

    def addExpense(self, anExpense):
        self._expenses.append(anExpense)
    
    def addIncome(self, anIncome):
        self._incomes.append(anIncome)
    
    def expenses(self):
        return self._expenses
    
    def incomes(self):
        return self._incomes

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