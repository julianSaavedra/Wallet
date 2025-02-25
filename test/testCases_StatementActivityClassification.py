from unittest import TestCase

from src.model_activityAggregation import ActivityAggregationDefinition, ActivityAggregationCompositeCondition, ActivityAggregationSpec
from src.model_activityAggregation import  ActivityDescriptionIncludesStringCondition, ActivityPluggableCondition
from src.model import AccountStatement, Dollars, StatementActivity
from test.testSupport import LoadedExpensesAndIncomesSource

class StatementActivityClassificationTest(TestCase):

    def testActivityAggregationIsEmptyIfThereAreNoExpensesAndEmptyAggregationSpecIsUsed(self):
        emptySource = LoadedExpensesAndIncomesSource()
        statement = AccountStatement.fromSource(emptySource)
        aggregationSpec = ActivityAggregationSpec.withDefinitions([])
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation, {})

    def testZeroDollarsAreAggregatedIntoSingleCategoryGroceriesIfThereIsNoActivity(self):
        emptySource = LoadedExpensesAndIncomesSource()
        statement = AccountStatement.fromSource(emptySource)
        groceriesCondition = lambda anActivity: 'MarketABC' in anActivity.description()
        groceriesDefinition = ActivityAggregationDefinition.withNameAndCondition('Groceries', groceriesCondition)
        aggregationSpec = ActivityAggregationSpec.withDefinition(groceriesDefinition)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries'].total(), Dollars.zero())

    def testZeroDollarsAreAggregatedIntoBothGroceriesAndServiciesCategoriesIfThereIsNoActivity(self):
        emptySource = LoadedExpensesAndIncomesSource()
        statement = AccountStatement.fromSource(emptySource)
        groceriesDefinition = ActivityAggregationDefinition.withNameAndCondition('Groceries', lambda anActivity: True)
        serviciesDefinition = ActivityAggregationDefinition.withNameAndCondition('Servicies', lambda anActivity: True)
        aggregationSpec = ActivityAggregationSpec.withDefinitions([groceriesDefinition, serviciesDefinition])
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries'].total(), Dollars.zero())
        self.assertEqual(activityAggregation['Servicies'].total(), Dollars.zero())

    def testSingleExpenseIsAggregatedToUnclassifiedWhenAnEmptyAggregationSpecIsUsed(self):
        twoDollars = Dollars.amount(2)
        anExpense = self.expenseWithDescriptionAndTotal('Description123', twoDollars)
        aSource = LoadedExpensesAndIncomesSource()
        aSource.addExpense(anExpense)
        statement = AccountStatement.fromSource(aSource)
        aggregationSpec = ActivityAggregationSpec.withDefinitions([])
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Unclassified'].total(), twoDollars)

    def testUnclassifiedCategoryIsTheOnlyCategoryWhenThereIsActivityAndAnEmptyAggregationSpecIsUsed(self):
        twoDollars = Dollars.amount(2)
        anExpense = self.expenseWithDescriptionAndTotal('Description123', twoDollars)
        aSource = LoadedExpensesAndIncomesSource()
        aSource.addExpense(anExpense)
        statement = AccountStatement.fromSource(aSource)
        aggregationSpec = ActivityAggregationSpec.withDefinitions([])
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(len(activityAggregation.keys()), 1)
        self.assertIn('Unclassified', activityAggregation.keys())

    def testSingleExpenseWhichDescriptionIncludingMarketABCIsClassifiedIntoGroceriesWithTotalOfTwoDollars(self):
        twoDollars = Dollars.amount(2)
        anExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        aSource = LoadedExpensesAndIncomesSource()
        aSource.addExpense(anExpense)
        statement = AccountStatement.fromSource(aSource)
        groceriesCondition = ActivityDescriptionIncludesStringCondition.forString('MarketABC')
        groceriesDefinition = ActivityAggregationDefinition.withNameAndCondition('Groceries', groceriesCondition)
        aggregationSpec = ActivityAggregationSpec.withDefinition(groceriesDefinition)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries'].total(),twoDollars)

    def testSingleExpenseIsAggregatedIntoGroceriesAndNotIntoServicesCategory(self):
        twoDollars = Dollars.amount(2)
        anExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        aSource = LoadedExpensesAndIncomesSource()
        aSource.addExpense(anExpense)
        statement = AccountStatement.fromSource(aSource)
        groceriesCondition = ActivityDescriptionIncludesStringCondition.forString('MarketABC')
        groceriesDefinition = ActivityAggregationDefinition.withNameAndCondition('Groceries', groceriesCondition)
        serviciesDefinition = ActivityAggregationDefinition.withNameAndCondition('Servicies', lambda anActivity: False)
        aggregationSpec = ActivityAggregationSpec.withDefinitions([groceriesDefinition, serviciesDefinition])
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries'].total(),twoDollars)
        self.assertEqual(activityAggregation['Servicies'].total(), Dollars.zero())

    def testSingleExpenseIsAggregatedIntoASingleGroceriesCategoryEvenIfMoreThanOneCategoriesWouldMatch(self):
        twoDollars = Dollars.amount(2)
        anExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        aSource = LoadedExpensesAndIncomesSource()
        aSource.addExpense(anExpense)
        statement = AccountStatement.fromSource(aSource)
        groceriesCondition_A = ActivityDescriptionIncludesStringCondition.forString('MarketABC')
        groceriesDefinition_A = ActivityAggregationDefinition.withNameAndCondition('Groceries_A', groceriesCondition_A)
        groceriesCondition_B = ActivityDescriptionIncludesStringCondition.forString('MarketABC')
        groceriesDefinition_B = ActivityAggregationDefinition.withNameAndCondition('Groceries_B', groceriesCondition_B)
        aggregationSpec = ActivityAggregationSpec.withDefinitions([groceriesDefinition_A, groceriesDefinition_B])
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries_A'].total(),twoDollars)
        self.assertEqual(activityAggregation['Groceries_B'].total(), Dollars.zero())

    def testSingleExpenseIsAggregatedToUnclassifiedWhenSingleGroceryCategoryDoesNotMatch(self):
        twoDollars = Dollars.amount(2)
        anExpense = self.expenseWithDescriptionAndTotal('Description123', twoDollars)
        aSource = LoadedExpensesAndIncomesSource()
        aSource.addExpense(anExpense)
        statement = AccountStatement.fromSource(aSource)
        groceriesCondition = ActivityPluggableCondition.usingCode(lambda anActivity: False)
        groceriesDefinition = ActivityAggregationDefinition.withNameAndCondition('Groceries', groceriesCondition)
        aggregationSpec = ActivityAggregationSpec.withDefinition(groceriesDefinition)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries'].total(), Dollars.zero())
        self.assertEqual(activityAggregation['Unclassified'].total(), twoDollars)

    def testUnclassifiedCategoryIsNotIncludedWhenSingleExpenseIsClassifiedIntoGroceries(self):
        twoDollars = Dollars.amount(2)
        anExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        aSource = LoadedExpensesAndIncomesSource()
        aSource.addExpense(anExpense)
        statement = AccountStatement.fromSource(aSource)
        groceriesCondition = ActivityDescriptionIncludesStringCondition.forString('MarketABC')
        groceriesDefinition = ActivityAggregationDefinition.withNameAndCondition('Groceries', groceriesCondition)
        aggregationSpec = ActivityAggregationSpec.withDefinition(groceriesDefinition)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries'].total(),twoDollars)
        self.assertNotIn('Unclassified', activityAggregation.keys())

    def testTwoExpensesAreAggregatedIntoUnclassifiedWithTotalOfFiveDollarsWhenEmptyAggregationSpecIsGiven(self):
        twoDollars = Dollars.amount(2)
        anExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        threeDollars = Dollars.amount(3)
        annotherExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', threeDollars)
        aSource = LoadedExpensesAndIncomesSource()
        aSource.addExpense(anExpense)
        aSource.addExpense(annotherExpense)
        statement = AccountStatement.fromSource(aSource)
        aggregationSpec = ActivityAggregationSpec.withDefinitions([])
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        fiveDollars = Dollars.amount(5)
        self.assertEqual(activityAggregation['Unclassified'].total(),fiveDollars)

    def testTwoExpensesWhichDescriptionsIncludeMarketABCAreClassifiedIntoGroceriesWithTotalOfFiveDollars(self):
        twoDollars = Dollars.amount(2)
        anExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        threeDollars = Dollars.amount(3)
        annotherExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', threeDollars)
        aSource = LoadedExpensesAndIncomesSource()
        aSource.addExpense(anExpense)
        aSource.addExpense(annotherExpense)
        statement = AccountStatement.fromSource(aSource)
        groceriesCondition = ActivityDescriptionIncludesStringCondition.forString('MarketABC')
        groceriesDefinition = ActivityAggregationDefinition.withNameAndCondition('Groceries', groceriesCondition)
        aggregationSpec = ActivityAggregationSpec.withDefinition(groceriesDefinition)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        fiveDollars = Dollars.amount(5)
        self.assertEqual(activityAggregation['Groceries'].total(),fiveDollars)

    def testOneTwoDollarsExpenseAggregatesIntoGroceriesAndAnotherFiveDollarsExpenseAggregatesToUnclassified(self):
        twoDollars = Dollars.amount(2)
        anExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        threeDollars = Dollars.amount(3)
        annotherExpense = self.expenseWithDescriptionAndTotal('Electrical Bill', threeDollars)
        aSource = LoadedExpensesAndIncomesSource()
        aSource.addExpense(anExpense)
        aSource.addExpense(annotherExpense)
        statement = AccountStatement.fromSource(aSource)
        groceriesCondition = ActivityDescriptionIncludesStringCondition.forString('MarketABC')
        groceriesDefinition = ActivityAggregationDefinition.withNameAndCondition('Groceries', groceriesCondition)
        aggregationSpec = ActivityAggregationSpec.withDefinition(groceriesDefinition)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries'].total(), twoDollars)
        self.assertEqual(activityAggregation['Unclassified'].total(), threeDollars)

    def testTwoExpensesAreAggregatedIntoUnclassifiedWithTotalOfFiveDollarsWhenSingleGroceryCategoryDoesNotMatch(self):
        twoDollars = Dollars.amount(2)
        anExpense = self.expenseWithDescriptionAndTotal('Expense_A', twoDollars)
        threeDollars = Dollars.amount(3)
        annotherExpense = self.expenseWithDescriptionAndTotal('Expense_B', threeDollars)
        aSource = LoadedExpensesAndIncomesSource()
        aSource.addExpense(anExpense)
        aSource.addExpense(annotherExpense)
        statement = AccountStatement.fromSource(aSource)
        alwaysFalseCondition = ActivityPluggableCondition.usingCode(lambda anActivity: False)
        groceriesDefinition = ActivityAggregationDefinition.withNameAndCondition('Groceries', alwaysFalseCondition)
        aggregationSpec = ActivityAggregationSpec.withDefinition(groceriesDefinition)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        fiveDollars = Dollars.amount(5)
        self.assertEqual(activityAggregation['Groceries'].total(),Dollars.zero())
        self.assertEqual(activityAggregation['Unclassified'].total(),fiveDollars)

    def testATwoDollarsExpenseGoesIntoGroceriesAndAnotherFiveDollarsExpenseGoesIntoServices(self):
        twoDollars = Dollars.amount(2)
        anExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        threeDollars = Dollars.amount(3)
        annotherExpense = self.expenseWithDescriptionAndTotal('Electrical Bill', threeDollars)
        aSource = LoadedExpensesAndIncomesSource()
        aSource.addExpense(anExpense)
        aSource.addExpense(annotherExpense)
        statement = AccountStatement.fromSource(aSource)
        groceriesCondition = ActivityDescriptionIncludesStringCondition.forString('MarketABC')
        groceriesDefinition = ActivityAggregationDefinition.withNameAndCondition('Groceries', groceriesCondition)
        servicesCondition = ActivityDescriptionIncludesStringCondition.forString('Electrical')
        serviciesDefinition = ActivityAggregationDefinition.withNameAndCondition('Servicies', servicesCondition)
        aggregationSpec = ActivityAggregationSpec.withDefinitions([groceriesDefinition, serviciesDefinition])
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries'].total(), twoDollars)
        self.assertEqual(activityAggregation['Servicies'].total(), threeDollars)

    def testTwoExpensesAreAggregatedIntoGroceriesWithTotalOfFiveDollarsAndServicesTotalsZeroDollars(self):
        twoDollars = Dollars.amount(2)
        anExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        threeDollars = Dollars.amount(3)
        annotherExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', threeDollars)
        aSource = LoadedExpensesAndIncomesSource()
        aSource.addExpense(anExpense)
        aSource.addExpense(annotherExpense)
        statement = AccountStatement.fromSource(aSource)
        groceriesCondition = ActivityDescriptionIncludesStringCondition.forString('MarketABC')
        groceriesDefinition = ActivityAggregationDefinition.withNameAndCondition('Groceries', groceriesCondition)
        servicesCondition = ActivityDescriptionIncludesStringCondition.forString('Electrical')
        serviciesDefinition = ActivityAggregationDefinition.withNameAndCondition('Servicies', servicesCondition)
        aggregationSpec = ActivityAggregationSpec.withDefinitions([groceriesDefinition, serviciesDefinition])
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        fiveDollars = Dollars.amount(5)
        self.assertEqual(activityAggregation['Groceries'].total(), fiveDollars)
        self.assertEqual(activityAggregation['Servicies'].total(), Dollars.zero())

    def testTwoExpensesAreAggregatedIntoUnclassifiedWhenBothGroceriesAndServicesCategoriesDoNotMatch(self):
        twoDollars = Dollars.amount(2)
        anExpense = self.expenseWithDescriptionAndTotal('Expense_A', twoDollars)
        threeDollars = Dollars.amount(3)
        annotherExpense = self.expenseWithDescriptionAndTotal('Expense_B', threeDollars)
        aSource = LoadedExpensesAndIncomesSource()
        aSource.addExpense(anExpense)
        aSource.addExpense(annotherExpense)
        statement = AccountStatement.fromSource(aSource)
        alwaysFalseCondition = ActivityPluggableCondition.usingCode(lambda anActivity: False)
        groceriesDefinition = ActivityAggregationDefinition.withNameAndCondition('Groceries', alwaysFalseCondition)
        serviciesDefinition = ActivityAggregationDefinition.withNameAndCondition('Servicies', alwaysFalseCondition)
        aggregationSpec = ActivityAggregationSpec.withDefinitions([groceriesDefinition, serviciesDefinition])
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        fiveDollars = Dollars.amount(5)
        self.assertEqual(activityAggregation['Groceries'].total(), Dollars.zero())
        self.assertEqual(activityAggregation['Servicies'].total(), Dollars.zero())
        self.assertEqual(activityAggregation['Unclassified'].total(), fiveDollars)

    def testThreeExpensesWithDifferentDescriptionsAreClassifiedIntoGroceriesWithTotalOfTwelveDollars(self):
        twoDollars = Dollars.amount(2)
        expenseA = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        threeDollars = Dollars.amount(3)
        expenseB = self.expenseWithDescriptionAndTotal('PayAPP XYZ_Fresh NY #R#', threeDollars)
        sevenDollars = Dollars.amount(7)
        expenseC = self.expenseWithDescriptionAndTotal('PayAPP Goods_4_You NY #R#', sevenDollars)
        aSource = LoadedExpensesAndIncomesSource()
        aSource.addExpense(expenseA)
        aSource.addExpense(expenseB)
        aSource.addExpense(expenseC)
        statement = AccountStatement.fromSource(aSource)
        groceriesSpecificConditions = [
            ActivityDescriptionIncludesStringCondition.forString('MarketABC'),
            ActivityDescriptionIncludesStringCondition.forString('XYZ_Fresh'),
            ActivityDescriptionIncludesStringCondition.forString('Goods_4_You'), ]
        groceriesCondition = ActivityAggregationCompositeCondition.withConditions(groceriesSpecificConditions)
        groceriesDefinition = ActivityAggregationDefinition.withNameAndCondition('Groceries', groceriesCondition)
        aggregationSpec = ActivityAggregationSpec.withDefinition(groceriesDefinition)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        twelveDollars = Dollars.amount(12)
        self.assertEqual(activityAggregation['Groceries'].total(),twelveDollars)

    def testThreeExpensesGoIntoUnclassifiedIfGroceriesConditionsAreEmpty(self):
        twoDollars = Dollars.amount(2)
        expenseA = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        threeDollars = Dollars.amount(3)
        expenseB = self.expenseWithDescriptionAndTotal('PayAPP XYZ_Fresh NY #R#', threeDollars)
        sevenDollars = Dollars.amount(7)
        expenseC = self.expenseWithDescriptionAndTotal('PayAPP Goods_4_You NY #R#', sevenDollars)
        aSource = LoadedExpensesAndIncomesSource()
        aSource.addExpense(expenseA)
        aSource.addExpense(expenseB)
        aSource.addExpense(expenseC)
        statement = AccountStatement.fromSource(aSource)
        groceriesCondition = ActivityAggregationCompositeCondition.withConditions([])
        groceriesDefinition = ActivityAggregationDefinition.withNameAndCondition('Groceries', groceriesCondition)
        aggregationSpec = ActivityAggregationSpec.withDefinition(groceriesDefinition)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        twelveDollars = Dollars.amount(12)
        self.assertEqual(activityAggregation['Groceries'].total(),Dollars.zero())
        self.assertEqual(activityAggregation['Unclassified'].total(),twelveDollars)

    def testActivityAggregationDefinitionCannotHaveAnEmptyName(self):
        aCondition = ActivityPluggableCondition.usingCode(lambda anActivity: False)
        with self.assertRaisesRegex(Exception, 'Category name cannot be empty'):
            ActivityAggregationDefinition.withNameAndCondition('', aCondition)

    def testActivityAggregationSpecCannotHaveMoreThanOneCategoryWithTheSameName(self):
        aCondition = ActivityPluggableCondition.usingCode(lambda anActivity: False)
        aCategoryDefiniton = ActivityAggregationDefinition.withNameAndCondition('Groceries', aCondition)
        anotherCategoryDefiniton = ActivityAggregationDefinition.withNameAndCondition('Groceries', aCondition)
        with self.assertRaisesRegex(Exception, 'Category names must be unique'):
            ActivityAggregationSpec.withDefinitions([aCategoryDefiniton, anotherCategoryDefiniton])

    def testStringInActivityDescriptionInclusionConditionCannotBeEmpty(self):
        with self.assertRaisesRegex(Exception, 'String to search for cannot be empty'):
            ActivityDescriptionIncludesStringCondition.forString('')
    
    def expenseWithDescriptionAndTotal(self, aDescription, aTotal):
        return StatementActivity.expenseWithDescriptionAndTotal(aDescription, aTotal)