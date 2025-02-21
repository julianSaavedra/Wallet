from unittest import TestCase
from collections import deque

from src.model import Dollars, AccountStatement, Expense, AccountStatementFileSource
from src.model import AccountStatementFileLineParser, SingleAmountColumnAccountStatementFileRecordSpecification, TwoAmountColumnsAccountStatementFileRecordSpecification
from test.testSupport import LoadedExpensesAndIncomesSource

class AccountStatementTest(TestCase):
  
    def testTotalExpenseFromStatementWithSourceWithNoExpensesIsZeroDollars(self):
        aSource = LoadedExpensesAndIncomesSource()
        statement = AccountStatement.fromSource(aSource)
        totalExpenses = statement.totalExpenses()
        self.assertEqual(totalExpenses, self.zeroDollars())
    
    def testTotalExpenseFromStatementWithSourceWithSingleExpenseIsTenDollars(self):
        tenDollars = self.dollars(10)
        aSource = self.sourceWithSingleExpense(tenDollars)
        statement = AccountStatement.fromSource(aSource)
        totalExpenses = statement.totalExpenses()
        self.assertEqual(totalExpenses, tenDollars)
    
    def testTotalExpenseFromStatementWithSourceWithTwoExpensesIsTwelveDollars(self):
        tenDollars = self.dollars(10)
        twoDollars = self.dollars(2)
        aSource = self.sourceWithExpenses([tenDollars, twoDollars])
        statement = AccountStatement.fromSource(aSource)
        totalExpenses = statement.totalExpenses()
        self.assertEqual(totalExpenses, self.dollars(12))
    
    def testTotalIncomeFromStatementWithSourceWithNoIncomesIsZeroDollars(self):
        aSource = LoadedExpensesAndIncomesSource()
        statement = AccountStatement.fromSource(aSource)
        totalIncome = statement.totalIncome()
        self.assertEqual(totalIncome, self.zeroDollars())

    def testTotalIncomeFromStatementWithSourceWithSingleIncomeIsFiftyDollars(self):
        fiftyDollars = self.dollars(50)
        aSource = self.sourceWithSingleIncome(fiftyDollars)
        statement = AccountStatement.fromSource(aSource)
        totalIncome = statement.totalIncome()
        self.assertEqual(totalIncome, fiftyDollars)

    def testTotalIncomeFromStatementWithSourceWithThreeIncomesIsThirtyNineDollars(self):
        threeDollars = self.dollars(3)
        tenDollars = self.dollars(10)
        twentySixDollars = self.dollars(26)
        aSource = self.sourceWithIncomes([threeDollars, tenDollars, twentySixDollars])
        statement = AccountStatement.fromSource(aSource)
        totalIncome = statement.totalIncome()
        self.assertEqual(totalIncome, self.dollars(39))

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
            anExpense = Expense.expenseWithTotal(anAmount)
            aSource.addExpense(anExpense)
        return aSource
    
    def sourceWithIncomes(self, amounts):
        aSource = LoadedExpensesAndIncomesSource()
        for anAmount in amounts:
            anExpense = Expense.incomeWithTotal(anAmount)
            aSource.addIncome(anExpense)
        return aSource

class AccountStatementFileSourceTest(TestCase):
    def testNoExpensesAreImportedFromEmptyFile(self):
        aFile = TestFile()
        parser = AccountStatementFileLineParser.commaSeparatedValues()
        spec = TwoAmountColumnsAccountStatementFileRecordSpecification.forColumns(descriptionColumn = 'Description', expenseColumn = 'Debit', incomeColumn = 'Credit')
        aSource = AccountStatementFileSource.fromFile(aFile, spec, parser)
        expenses = aSource.expenses()
        self.assertEqual(len(expenses),0)
    
    def testNoIncomesAreImportedFromEmptyFile(self):
        aFile = TestFile()
        parser = AccountStatementFileLineParser.commaSeparatedValues()
        spec = TwoAmountColumnsAccountStatementFileRecordSpecification.forColumns(descriptionColumn = 'Description', expenseColumn = 'Debit', incomeColumn = 'Credit')
        aSource = AccountStatementFileSource.fromFile(aFile, spec, parser)
        incomes = aSource.incomes()
        self.assertEqual(len(incomes),0)
    
    def testSingleExpenseOfTwoDollarsIsImportedFromFile(self):
        aFile = TestFile()
        aFile.addLine('Date,Description,Debit,Credit\n')
        aFile.addLine('09-27-2024,PurchaseA,2.00,\n')
        parser = AccountStatementFileLineParser.commaSeparatedValues()
        spec = TwoAmountColumnsAccountStatementFileRecordSpecification.forColumns(descriptionColumn = 'Description', expenseColumn = 'Debit', incomeColumn = 'Credit')
        aSource = AccountStatementFileSource.fromFile(aFile, spec, parser)
        expenses = aSource.expenses()
        self.assertActivitiesQuantity(expenses, 1)
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'PurchaseA', 2)
    
    def testThreeExpensesOfTwoSixAndTenDollarsAreImportedFromFile(self):
        aFile = TestFile()
        aFile.addLine('Date,Description,Debit,Credit')
        aFile.addLine('09-27-2024,PurchaseA,2.00,')
        aFile.addLine('09-27-2024,PurchaseB,6.00,')
        aFile.addLine('09-27-2024,PurchaseC,10.00,')
        parser = AccountStatementFileLineParser.commaSeparatedValues()
        spec = TwoAmountColumnsAccountStatementFileRecordSpecification.forColumns(descriptionColumn = 'Description', expenseColumn = 'Debit', incomeColumn = 'Credit')
        aSource = AccountStatementFileSource.fromFile(aFile, spec, parser)
        expenses = aSource.expenses()
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'PurchaseA', 2)
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'PurchaseB', 6)
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'PurchaseC', 10)
    
    def testSingleIncomeOfSevenDollarsIsImportedFromFile(self):
        aFile = TestFile()
        aFile.addLine('Date,Description,Debit,Credit')
        aFile.addLine('09-30-2024,IncomeA,,7.85')
        parser = AccountStatementFileLineParser.commaSeparatedValues()
        spec = TwoAmountColumnsAccountStatementFileRecordSpecification.forColumns(descriptionColumn = 'Description', expenseColumn = 'Debit', incomeColumn = 'Credit')
        aSource = AccountStatementFileSource.fromFile(aFile, spec, parser)
        incomes = aSource.incomes()
        self.assertActivityWithDescriptionAndTotalInDollars(incomes, 'IncomeA', 7.85)
    
    def testThreeIncomesOfTenTwelveAndTwentyDollarsAreImportedFromFile(self):
        aFile = TestFile()
        aFile.addLine('Date,Description,Debit,Credit')
        aFile.addLine('09-30-2024,IncomeA,,10.00')
        aFile.addLine('09-30-2024,IncomeB,,12.00')
        aFile.addLine('09-30-2024,IncomeC,,20.00')
        parser = AccountStatementFileLineParser.commaSeparatedValues()
        spec = TwoAmountColumnsAccountStatementFileRecordSpecification.forColumns(descriptionColumn = 'Description', expenseColumn = 'Debit', incomeColumn = 'Credit')
        aSource = AccountStatementFileSource.fromFile(aFile, spec, parser)
        incomes = aSource.incomes()
        self.assertActivityWithDescriptionAndTotalInDollars(incomes, 'IncomeA', 10)
        self.assertActivityWithDescriptionAndTotalInDollars(incomes, 'IncomeB', 12)
        self.assertActivityWithDescriptionAndTotalInDollars(incomes, 'IncomeC', 20)
    
    def testTwoIncomesOfTwoAndFourDollarsAndTwoExpensesOfThreeAndFiveAreImportedFromFile(self):
        aFile = TestFile()
        aFile.addLine('Date,Description,Debit,Credit')
        aFile.addLine('09-30-2024,IncomeA,,2.00')
        aFile.addLine('09-27-2024,PurchaseA,3.00,')        
        aFile.addLine('09-30-2024,IncomeB,,4.00')
        aFile.addLine('09-27-2024,PurchaseB,5.00,')
        parser = AccountStatementFileLineParser.commaSeparatedValues()
        spec = TwoAmountColumnsAccountStatementFileRecordSpecification.forColumns(descriptionColumn = 'Description', expenseColumn = 'Debit', incomeColumn = 'Credit')
        aSource = AccountStatementFileSource.fromFile(aFile, spec, parser)
        expenses = aSource.expenses()
        incomes = aSource.incomes()
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'PurchaseA', 3)
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'PurchaseB', 5)
        self.assertActivityWithDescriptionAndTotalInDollars(incomes, 'IncomeA', 2)
        self.assertActivityWithDescriptionAndTotalInDollars(incomes, 'IncomeB', 4)
    
    def testSingleExpenseOfThreeDollarsIsImportedFromFileWithSingleAmountColumn(self):
        aFile = TestFile()
        aFile.addLine('Date,Description,Card Member,Account #,Amount\n')
        aFile.addLine('12/05/2024,Subway,Name LastName,-13006,3.00\n')
        spec = SingleAmountColumnAccountStatementFileRecordSpecification.forSpecificColumn(descriptionColumn = 'Description', amountColumn = 'Amount')
        parser = AccountStatementFileLineParser.commaSeparatedValues()
        aSource = AccountStatementFileSource.fromFile(aFile, spec, parser)
        expenses = aSource.expenses()
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'Subway', 3)
    
    def testSingleIncomeOfFiveDollarsIsImportedFromFileWithSingleAmountColumn(self):
        aFile = TestFile()
        aFile.addLine('Date,Description,Card Member,Account #,Amount\n')
        aFile.addLine('12/10/2024,Payment,Name LastName,-13006,-5.00\n')
        spec = SingleAmountColumnAccountStatementFileRecordSpecification.forSpecificColumn(descriptionColumn = 'Description', amountColumn = 'Amount')
        parser = AccountStatementFileLineParser.commaSeparatedValues()
        aSource = AccountStatementFileSource.fromFile(aFile, spec, parser)
        incomes = aSource.incomes()
        self.assertActivityWithDescriptionAndTotalInDollars(incomes, 'Payment', 5)
    
    def testTwoIncomesOfTwoAndFourDollarsAndTwoExpensesOfThreeAndFiveAreImportedFromFileWithSingleAmountColumn(self):
        aFile = TestFile()
        aFile.addLine('Date,Description,Card Member,Account #,Amount\n')
        aFile.addLine('12/05/2024,Subway,Name LastName,-13006,3.00\n')
        aFile.addLine('12/10/2024,Payment,Name LastName,-13006,-2.00\n')
        aFile.addLine('12/05/2024,Coffee,Name LastName,-13006,5.00\n')
        aFile.addLine('12/10/2024,Payment,Name LastName,-13006,-4.00\n')
        spec = SingleAmountColumnAccountStatementFileRecordSpecification.forSpecificColumn(descriptionColumn = 'Description', amountColumn = 'Amount')
        parser = AccountStatementFileLineParser.commaSeparatedValues()
        aSource = AccountStatementFileSource.fromFile(aFile, spec, parser)
        expenses = aSource.expenses()
        incomes = aSource.incomes()
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'Subway', 3)
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'Coffee', 5)
        self.assertActivityWithDescriptionAndTotalInDollars(incomes, 'Payment', 2)
        self.assertActivityWithDescriptionAndTotalInDollars(incomes, 'Payment', 4)

    def assertActivitiesQuantity(self, activities, expectedSize):
        self.assertEqual(len(activities), expectedSize)
    
    def assertActivityWithDescriptionAndTotalInDollars(self, activities, aDescription, aDollarAmount):
        matchingActivityWasFound = False
        expectedActivityTotal = Dollars.amount(aDollarAmount)
        for anActivity in activities:
            currentActivityMatchesDescription = anActivity.description() == aDescription
            currentActivityMatchesTotal = anActivity.total() == expectedActivityTotal
            currentActivityMatches = currentActivityMatchesDescription and currentActivityMatchesTotal
            matchingActivityWasFound = matchingActivityWasFound or currentActivityMatches
        self.assertTrue(matchingActivityWasFound, 'No matching activity with expected description and total')
    
    def assertAllAndOnlyTotalsInDollars(self, activities, expectedDollarAmounts):
        self.assertEqual(len(activities), len(expectedDollarAmounts))
        for activity , expectedDollarAmount in zip(activities, expectedDollarAmounts):
            self.assertEqual(activity.total(), Dollars.amount(expectedDollarAmount))
        

class AccountStatementFileLineParserTest(TestCase):
    def testLineWithFourCommaSeparatedValuesIsParsedIntoAListWithThoseFourValues(self):
        parser = AccountStatementFileLineParser.commaSeparatedValues()
        parsedLine = parser.parse('A,$,Hello,1.0')
        self.assertEqual(parsedLine, ['A', '$', 'Hello', '1.0'])

    def testLineWithNoValueAfterTheFirstCommaIsParsedIntoAListWithAnEmptyStringsInSecondPlace(self):
        parser = AccountStatementFileLineParser.commaSeparatedValues()
        parsedLine = parser.parse('A,,Hello,1.0')
        self.assertEqual(parsedLine, ['A', '', 'Hello', '1.0'])

    def testLineWithNoValueAfterLastCommaIsParsedIntoAListWithAnEmptyStringAtTheEnd(self):
        parser = AccountStatementFileLineParser.commaSeparatedValues()
        parsedLine = parser.parse('A,$,Hello,')
        self.assertEqual(parsedLine, ['A', '$', 'Hello', ''])
    
    def testLineWithNoValueBeforeFirstCommaIsParsedIntoAListWithAnEmptyStringAtTheFirstPlace(self):
        parser = AccountStatementFileLineParser.commaSeparatedValues()
        parsedLine = parser.parse(',$,Hello,1.0')
        self.assertEqual(parsedLine, ['', '$', 'Hello', '1.0'])
    
    def testWhiteSpacesAtTheStartOrEndOfCommaSeparatedValuesAreIgnored(self):
        parser = AccountStatementFileLineParser.commaSeparatedValues()
        parsedLine = parser.parse('A,$ , Hello World,1.0\n')
        self.assertEqual(parsedLine, ['A', '$', 'Hello World', '1.0'])
    
    def testLinesSectionWithCommaWithinQuotesIsParsedAsASingleValue(self):
        parser = AccountStatementFileLineParser.commaSeparatedValues(boundingCharacter='"')
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