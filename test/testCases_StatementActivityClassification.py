from unittest import TestCase

from src.model import FinancialActivityStatement, Dollars, FinancialActivity
from src.model_activityAggregation import ActivityAggregationSpec
from src.model_activityEnrichment import ActivityAggregationCompositeCondition, ActivityAggregationDefinition
from src.model_activityEnrichment import  ActivityDescriptionIncludesStringCondition, ActivityPluggableCondition
from src.model_activityEnrichment import ActivityEnrichmentSpecBuilder
from test.testSupport import LoadedActivitySource

#DescriptionOverride can be empty? it would use the original one?
#DifferentConditionsFor same override/bucket
#Goal - rename the original AggregationSpecs?

class StatementActivityClassificationTest(TestCase):

    def testActivityAggregationIsEmptyIfThereAreNoExpensesAndEmptyAggregationSpecIsUsed(self):
        statement = self.emptyStatement()
        activityEnrichmentSpec = self.emptySpec()
        aggregationSpec = ActivityAggregationSpec.withEnrichmentActivitySpec(activityEnrichmentSpec)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation, {})

    def testZeroDollarsAreAggregatedIntoSingleCategoryGroceriesIfThereIsNoActivity(self):
        emptySource = self.emptySource()
        statement = FinancialActivityStatement.fromSingleSource(emptySource)
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForDescriptionIncludingString('Groceries', 'MarketABC','Markt#ABC')
        activityEnrichmentSpec = specBuilder.fullSpec()
        aggregationSpec = ActivityAggregationSpec.withEnrichmentActivitySpec(activityEnrichmentSpec)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries'].total(), Dollars.zero())

    def testZeroDollarsAreAggregatedIntoBothGroceriesAndServiciesCategoriesIfThereIsNoActivity(self):
        statement = self.emptyStatement()
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForCodeBasedCondition('Groceries', 'MarketABC', lambda anActivity: True)
        specBuilder.addDefintionSpecForCodeBasedCondition('Servicies', 'ServiceProvider', lambda anActivity: True)
        activityEnrichmentSpec = specBuilder.fullSpec()
        aggregationSpec = ActivityAggregationSpec.withEnrichmentActivitySpec(activityEnrichmentSpec)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries'].total(), Dollars.zero())
        self.assertEqual(activityAggregation['Servicies'].total(), Dollars.zero())

    def testSingleExpenseIsAggregatedToUnclassifiedWhenAnEmptyAggregationSpecIsUsed(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithDescriptionAndTotal('Description123', twoDollars)
        aSource = LoadedActivitySource.withActivity(anExpense)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        specBuilder = ActivityEnrichmentSpecBuilder()
        activityEnrichmentSpec = specBuilder.fullSpec()
        aggregationSpec = ActivityAggregationSpec.withEnrichmentActivitySpec(activityEnrichmentSpec)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Unclassified'].total(), twoDollars)

    def testUnclassifiedCategoryIsTheOnlyCategoryWhenThereIsActivityAndAnEmptyAggregationSpecIsUsed(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithDescriptionAndTotal('Description123', twoDollars)
        aSource = LoadedActivitySource.withActivity(anExpense)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        specBuilder = ActivityEnrichmentSpecBuilder()
        activityEnrichmentSpec = specBuilder.fullSpec()
        aggregationSpec = ActivityAggregationSpec.withEnrichmentActivitySpec(activityEnrichmentSpec)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(len(activityAggregation.keys()), 1)
        self.assertIn('Unclassified', activityAggregation.keys())

    def testSingleExpenseWhichDescriptionIncludingMarketABCIsClassifiedIntoGroceriesWithTotalOfTwoDollars(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        aSource = LoadedActivitySource.withActivity(anExpense)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForDescriptionIncludingString('Groceries', 'MarketABC', 'MarketABC')
        activityEnrichmentSpec = specBuilder.fullSpec()
        aggregationSpec = ActivityAggregationSpec.withEnrichmentActivitySpec(activityEnrichmentSpec)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries'].total(),twoDollars)

    def testSingleExpenseIsAggregatedIntoGroceriesAndNotIntoServicesCategory(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        aSource = LoadedActivitySource()
        aSource.addExpense(anExpense)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForDescriptionIncludingString('Groceries', 'MarketABC', 'MarketABC')
        specBuilder.addDefintionSpecForCodeBasedCondition('Servicies', 'ServiceProvider', lambda anActivity: False)
        activityEnrichmentSpec = specBuilder.fullSpec()
        aggregationSpec = ActivityAggregationSpec.withEnrichmentActivitySpec(activityEnrichmentSpec)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries'].total(),twoDollars)
        self.assertEqual(activityAggregation['Servicies'].total(), Dollars.zero())

    def testSingleExpenseIsAggregatedIntoASingleGroceriesCategoryEvenIfMoreThanOneCategoriesWouldMatch(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        aSource = LoadedActivitySource()
        aSource.addExpense(anExpense)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForDescriptionIncludingString('Groceries_A', 'MarketABC', 'MarketABC')
        specBuilder.addDefintionSpecForDescriptionIncludingString('Groceries_B', 'MarketABC', 'MarketABC')
        activityEnrichmentSpec = specBuilder.fullSpec()
        aggregationSpec = ActivityAggregationSpec.withEnrichmentActivitySpec(activityEnrichmentSpec)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries_A'].total(),twoDollars)
        self.assertEqual(activityAggregation['Groceries_B'].total(), Dollars.zero())

    def testSingleExpenseIsAggregatedToUnclassifiedWhenSingleGroceryCategoryDoesNotMatch(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithDescriptionAndTotal('Description123', twoDollars)
        aSource = LoadedActivitySource()
        aSource.addExpense(anExpense)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForCodeBasedCondition('Groceries', 'GroceriesPlace', lambda anActivity: False)
        activityEnrichmentSpec = specBuilder.fullSpec()
        aggregationSpec = ActivityAggregationSpec.withEnrichmentActivitySpec(activityEnrichmentSpec)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries'].total(), Dollars.zero())
        self.assertEqual(activityAggregation['Unclassified'].total(), twoDollars)

    def testUnclassifiedCategoryIsNotIncludedWhenSingleExpenseIsClassifiedIntoGroceries(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        aSource = LoadedActivitySource()
        aSource.addExpense(anExpense)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForDescriptionIncludingString('Groceries', 'MarketABC', 'MarketABC')
        activityEnrichmentSpec = specBuilder.fullSpec()
        aggregationSpec = ActivityAggregationSpec.withEnrichmentActivitySpec(activityEnrichmentSpec)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries'].total(),twoDollars)
        self.assertNotIn('Unclassified', activityAggregation.keys())

    def testTwoExpensesAreAggregatedIntoUnclassifiedWithTotalOfFiveDollarsWhenEmptyAggregationSpecIsGiven(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        threeDollars = self.dollars(3)
        annotherExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', threeDollars)
        aSource = LoadedActivitySource.withActivities([anExpense, annotherExpense])
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        specBuilder = ActivityEnrichmentSpecBuilder()
        activityEnrichmentSpec = specBuilder.fullSpec()
        aggregationSpec = ActivityAggregationSpec.withEnrichmentActivitySpec(activityEnrichmentSpec)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        fiveDollars = self.dollars(5)
        self.assertEqual(activityAggregation['Unclassified'].total(),fiveDollars)

    def testTwoExpensesWhichDescriptionsIncludeMarketABCAreClassifiedIntoGroceriesWithTotalOfFiveDollars(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        threeDollars = self.dollars(3)
        annotherExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', threeDollars)
        aSource = LoadedActivitySource.withActivities([anExpense, annotherExpense])
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForDescriptionIncludingString('Groceries', 'MarketABC', 'MarketABC')
        activityEnrichmentSpec = specBuilder.fullSpec()
        aggregationSpec = ActivityAggregationSpec.withEnrichmentActivitySpec(activityEnrichmentSpec)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        fiveDollars = self.dollars(5)
        self.assertEqual(activityAggregation['Groceries'].total(),fiveDollars)

    def testOneTwoDollarsExpenseAggregatesIntoGroceriesAndAnotherFiveDollarsExpenseAggregatesToUnclassified(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        threeDollars = self.dollars(3)
        annotherExpense = self.expenseWithDescriptionAndTotal('Electrical Bill', threeDollars)
        aSource = LoadedActivitySource.withActivities([anExpense, annotherExpense])
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForDescriptionIncludingString('Groceries', 'MarketABC', 'MarketABC')
        activityEnrichmentSpec = specBuilder.fullSpec()
        aggregationSpec = ActivityAggregationSpec.withEnrichmentActivitySpec(activityEnrichmentSpec)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries'].total(), twoDollars)
        self.assertEqual(activityAggregation['Unclassified'].total(), threeDollars)

    def testTwoExpensesAreAggregatedIntoUnclassifiedWithTotalOfFiveDollarsWhenSingleGroceryCategoryDoesNotMatch(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithDescriptionAndTotal('Expense_A', twoDollars)
        threeDollars = self.dollars(3)
        annotherExpense = self.expenseWithDescriptionAndTotal('Expense_B', threeDollars)
        aSource = LoadedActivitySource.withActivities([anExpense, annotherExpense])
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForCodeBasedCondition('Groceries', 'MarketABC', lambda anActivity: False)
        activityEnrichmentSpec = specBuilder.fullSpec()
        aggregationSpec = ActivityAggregationSpec.withEnrichmentActivitySpec(activityEnrichmentSpec)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        fiveDollars = self.dollars(5)
        self.assertEqual(activityAggregation['Groceries'].total(),Dollars.zero())
        self.assertEqual(activityAggregation['Unclassified'].total(),fiveDollars)

    def testATwoDollarsExpenseGoesIntoGroceriesAndAnotherFiveDollarsExpenseGoesIntoServices(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        threeDollars = self.dollars(3)
        anotherExpense = self.expenseWithDescriptionAndTotal('Electrical Bill', threeDollars)
        aSource = LoadedActivitySource.withActivities([anExpense, anotherExpense])
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForDescriptionIncludingString('Groceries', 'MarketABC', 'MarketABC')
        specBuilder.addDefintionSpecForDescriptionIncludingString('Servicies', 'Electricity', 'Electrical')
        activityEnrichmentSpec = specBuilder.fullSpec()
        aggregationSpec = ActivityAggregationSpec.withEnrichmentActivitySpec(activityEnrichmentSpec)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries'].total(), twoDollars)
        self.assertEqual(activityAggregation['Servicies'].total(), threeDollars)

    def testTwoExpensesAreAggregatedIntoGroceriesWithTotalOfFiveDollarsAndServicesTotalsZeroDollars(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        threeDollars = self.dollars(3)
        annotherExpense = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', threeDollars)
        aSource = LoadedActivitySource()
        aSource.addExpense(anExpense)
        aSource.addExpense(annotherExpense)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForDescriptionIncludingString('Groceries', 'MarketABC', 'MarketABC')
        specBuilder.addDefintionSpecForDescriptionIncludingString('Servicies', 'Electricity', 'Electrical')
        activityEnrichmentSpec = specBuilder.fullSpec()
        aggregationSpec = ActivityAggregationSpec.withEnrichmentActivitySpec(activityEnrichmentSpec)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        fiveDollars = self.dollars(5)
        self.assertEqual(activityAggregation['Groceries'].total(), fiveDollars)
        self.assertEqual(activityAggregation['Servicies'].total(), Dollars.zero())

    def testTwoExpensesAreAggregatedIntoUnclassifiedWhenBothGroceriesAndServicesCategoriesDoNotMatch(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithDescriptionAndTotal('Expense_A', twoDollars)
        threeDollars = self.dollars(3)
        annotherExpense = self.expenseWithDescriptionAndTotal('Expense_B', threeDollars)
        aSource = LoadedActivitySource.withActivities([anExpense, annotherExpense])
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForCodeBasedCondition('Groceries', 'GroceriesPlace', lambda anActivity: False)
        specBuilder.addDefintionSpecForCodeBasedCondition('Servicies', 'ServiceCompany', lambda anActivity: False)
        activityEnrichmentSpec = specBuilder.fullSpec()
        aggregationSpec = ActivityAggregationSpec.withEnrichmentActivitySpec(activityEnrichmentSpec)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        fiveDollars = self.dollars(5)
        self.assertEqual(activityAggregation['Groceries'].total(), Dollars.zero())
        self.assertEqual(activityAggregation['Servicies'].total(), Dollars.zero())
        self.assertEqual(activityAggregation['Unclassified'].total(), fiveDollars)

    def testThreeExpensesWithDifferentDescriptionsAreClassifiedIntoGroceriesWithTotalOfTwelveDollars(self):
        twoDollars = self.dollars(2)
        expenseA = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        threeDollars = self.dollars(3)
        expenseB = self.expenseWithDescriptionAndTotal('PayAPP XYZ_Fresh NY #R#', threeDollars)
        sevenDollars = self.dollars(7)
        expenseC = self.expenseWithDescriptionAndTotal('PayAPP Goods_4_You NY #R#', sevenDollars)
        aSource = LoadedActivitySource.withActivities([expenseA, expenseB, expenseC])
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        specBuilder = ActivityEnrichmentSpecBuilder()
        groceryConditionStrings = ['MarketABC', 'XYZ_Fresh', 'Goods_4_You']
        specBuilder.addDefintionSpecForDescriptionIncludingAnyOfGivenStrings('Groceries', 'GroceriesPlace', groceryConditionStrings)
        activityEnrichmentSpec = specBuilder.fullSpec()
        aggregationSpec = ActivityAggregationSpec.withEnrichmentActivitySpec(activityEnrichmentSpec)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        twelveDollars = self.dollars(12)
        self.assertEqual(activityAggregation['Groceries'].total(),twelveDollars)

    def testThreeExpensesGoIntoUnclassifiedIfGroceriesConditionsAreEmpty(self):
        twoDollars = self.dollars(2)
        expenseA = self.expenseWithDescriptionAndTotal('PayAPP MarketABC NY #R#', twoDollars)
        threeDollars = self.dollars(3)
        expenseB = self.expenseWithDescriptionAndTotal('PayAPP XYZ_Fresh NY #R#', threeDollars)
        sevenDollars = self.dollars(7)
        expenseC = self.expenseWithDescriptionAndTotal('PayAPP Goods_4_You NY #R#', sevenDollars)
        aSource = LoadedActivitySource.withActivities([expenseA, expenseB, expenseC])
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForCodeBasedCondition('Groceries', 'GroceriesPlace', lambda anActivity: False)
        activityEnrichmentSpec = specBuilder.fullSpec()
        aggregationSpec = ActivityAggregationSpec.withEnrichmentActivitySpec(activityEnrichmentSpec)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        twelveDollars = self.dollars(12)
        self.assertEqual(activityAggregation['Groceries'].total(),Dollars.zero())
        self.assertEqual(activityAggregation['Unclassified'].total(),twelveDollars)

    def testActivityAggregationDefinitionCannotHaveAnEmptyName(self):
        aCondition = ActivityPluggableCondition.usingCode(lambda anActivity: False)
        with self.assertRaisesRegex(Exception, 'Category name cannot be empty'):
            ActivityAggregationDefinition.withNameAndCondition('', aCondition)

    def testStringInActivityDescriptionInclusionConditionCannotBeEmpty(self):
        with self.assertRaisesRegex(Exception, 'String to search for cannot be empty'):
            ActivityDescriptionIncludesStringCondition.forString('')
    
    def dollars(self, aTotalAmountInDollars):
        return Dollars.withAmount(aTotalAmountInDollars)

    def expenseWithDescriptionAndTotal(self, aDescription, aTotal):
        return FinancialActivity.expenseWithDescriptionAndTotal(aDescription, 'BananinYBananon', aTotal)

    def emptySpec(self):
        specBuilder = ActivityEnrichmentSpecBuilder()
        return specBuilder.fullSpec()

    def emptyStatement(self):
        emptySource = self.emptySource()
        statement = FinancialActivityStatement.fromSingleSource(emptySource)
        return statement

    def emptySource(self):
        return LoadedActivitySource()

class ActivityEnrichmentSpecBuilderTest(TestCase):  

    def testBucketNameCannotBeEmpty(self):
        specBuilder = ActivityEnrichmentSpecBuilder()
        with self.assertRaisesRegex(Exception, 'Bucket name cannot be empty'):
            specBuilder.addDefintionSpecForDescriptionIncludingString('', 'DescriptionOverride','StringInDescription')
    
    def testAddingADefinitionFailsIfAPreviousDefinitionsWithTheSameBucketAlreadyExists(self):
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForDescriptionIncludingString('Bucket_A', 'DescriptionOverride','StringInDescription')
        with self.assertRaisesRegex(Exception, 'Definition for same bucket already exists'):
            specBuilder.addDefintionSpecForDescriptionIncludingString('Bucket_A', 'AnotherDescriptionOverride','AnotherStringInDescription')