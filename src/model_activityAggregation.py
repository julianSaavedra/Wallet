from src.model import Dollars, FinancialActivity

class ActivityAggregationSpec:

    @classmethod
    def withEnrichmentActivitySpec(cls, spec):
        return cls(None, spec)

    @classmethod
    def withDefinitions(cls, definitions):
       """ cls.assertUniqueCategories(definitions)
        return cls(definitions, None)"""

    @classmethod
    def withDefinition(cls, definition):
        return cls.withDefinitions([definition])

    @classmethod
    def assertUniqueCategories(cls,definitions):
        categoryNames = [aDefinition.category() for aDefinition in definitions]
        if not len(definitions) == len(set(categoryNames)):
            raise Exception('Category names must be unique')

    def __init__(self, definitions, spec):
        self._definitions = definitions
        self._spec = spec

    def aggregatedResultsFromActivities(self, activities):
        if self._spec:
            aggregatedActivities = self.aggregatedActivitiesWITHSPECBANANA(activities)
        else:
            aggregatedActivities = self.aggregatedActivities(activities)
        return self.totalsFromAggregatedActivities(aggregatedActivities)

    def aggregatedActivitiesWITHSPECBANANA(self, activities):
        aggregation = { bucket:[] for bucket in self._spec.allBuckets() }
        enrichedActivities = [self._spec.newEnrichedActivity(anActivity) for anActivity in activities]
        for anActivity in enrichedActivities:
            if anActivity.bucket() in aggregation:
                aggregation[anActivity.category()].append(anActivity)
            else: aggregation[anActivity.category()] = [ anActivity ]
        return aggregation

    def aggregatedActivities(self, activities):
        aggregation = {}
        remainingActivities = activities.copy()
        for aDefinition in self._definitions:
            matchingActivities = [ anActivity for anActivity in remainingActivities if aDefinition.matches(anActivity)]
            aggregation[aDefinition.category()] = matchingActivities
            for matchedActivity in matchingActivities: remainingActivities.remove(matchedActivity)
        if remainingActivities: aggregation['Unclassified'] = remainingActivities
        return aggregation

    def totalsFromAggregatedActivities(self, aggregatedActivities):
        totalsAggregation = {}
        for category, activities in aggregatedActivities.items():
            totalForCategory = Dollars.zero()
            for anActivity in activities: totalForCategory = totalForCategory + anActivity.total()
            totalsAggregation[category] = FinancialActivity.expenseWithTotal(totalForCategory)
        return totalsAggregation
