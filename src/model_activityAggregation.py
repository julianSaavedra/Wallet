from src.model import Dollars, StatementActivity


class ActivityAggregationSpec:

    @classmethod
    def withDefinitions(cls, definitions):
        cls.assertUniqueCategories(definitions)
        return cls(definitions)

    @classmethod
    def withDefinition(cls, definition):
        return cls.withDefinitions([definition])

    @classmethod
    def assertUniqueCategories(cls,definitions):
        categoryNames = [aDefinition.category() for aDefinition in definitions]
        if not len(definitions) == len(set(categoryNames)):
            raise Exception('Category names must be unique')

    def __init__(self, definitions):
        self._definitions = definitions

    def aggregatedResultsFromActivities(self, activities):
        aggregatedActivities = self.aggregatedActivities(activities)
        return self.totalsFromAggregatedActivities(aggregatedActivities)

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
            totalsAggregation[category] = StatementActivity.expenseWithTotal(totalForCategory)
        return totalsAggregation


class ActivityAggregationCompositeCondition:

    @classmethod
    def withConditions(cls, conditions):
        return cls(conditions)

    def __init__(self, conditions):
        self._conditions = conditions

    def satisfies(self, anActivity):
        return any([aCondition.satisfies(anActivity) for aCondition in self._conditions])


class ActivityPluggableCondition:

    @classmethod
    def usingCode(cls, code):
        return cls(code)

    def __init__(self, code):
        self._code = code

    def satisfies(self, anActivity):
        return self._code(anActivity)


class ActivityDescriptionIncludesStringCondition:

    @classmethod
    def forString(cls, aString):
        cls.assertValid(aString)
        return cls(aString)

    @classmethod
    def assertValid(cls, aString):
        if not aString: raise Exception('String to search for cannot be empty')

    def __init__(self, aString):
        self._string = aString

    def satisfies(self, anActivity):
        return self._string in anActivity.description()


class ActivityAggregationDefinition:

    @classmethod
    def withNameAndCondition(cls, name, condition):
        cls.assertName(name)
        return cls(name, condition)

    @classmethod
    def assertName(cls, name):
        if not name: raise Exception('Category name cannot be empty')

    def __init__(self, name, condition):
        self._name = name
        self._condition = condition

    def category(self):
        return self._name

    def matches(self, anActivity):
        return self._condition.satisfies(anActivity)


class ActivityEnrichment():

    @classmethod
    def fromStatement(cls, aStatement):
        return cls(aStatement)
    
    def __init__(self, aStatement):
        self._statement = aStatement 

    def results(self):
        return [EnrichedActivity.withDescriptionAndBucket('Description123', 'NoBucket') for anActivity in self._statement.allActivities()]


class EnrichedActivity():

    @classmethod
    def withDescriptionAndBucket(cls, description, bucket):
        return cls(description, bucket)
    
    def __init__(self, description, bucket):
        self._description = description
        self._bucket = bucket

    def description(self):
        return self._description
    
    def bucket(self):
        return self._bucket