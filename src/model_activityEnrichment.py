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


class RawActivityRecord():
    
    @classmethod
    def withDescription(cls, description):
        return cls(description)
    
    def __init__(self, description):
        self._description = description
    
    def description(self):
        return self._description

class ActivityEnrichmentSpec():
     
    @classmethod
    def withDefinitions(cls, definitions):
        return cls(definitions)
    
    @classmethod
    def empty(cls):
        return cls.withDefinitions([])

    def __init__(self, definitions):
        self._definitions = definitions
        
    def enrichmentDefinitionForRawDescription(self, rawDescription):
        rawRecord = RawActivityRecord.withDescription(rawDescription)
        for aDefinition in self._definitions:
            if aDefinition.matches(rawRecord): return aDefinition
        return ActivityEnrichmentSpecDefinition.withBucketDescriptionOverrideAndCondition('Unclassified', rawDescription, None)

    def allBuckets(self):
        return [aDefinition.bucket() for aDefinition in self._definitions]


class ActivityEnrichmentSpecDefinition():

    @classmethod
    def withBucketDescriptionOverrideAndCondition(cls, bucket, descriptionOverride, condition):
        cls.assertBucket(bucket)
        return cls(bucket, descriptionOverride, condition)

    @classmethod
    def assertBucket(cls, bucket):
        if not bucket: raise Exception('Bucket name cannot be empty')

    def __init__(self, bucket, descriptionOverride, condition):
        self._bucket = bucket
        self._descriptionOverride = descriptionOverride
        self._condition = condition

    def descriptionOverride(self):
        return self._descriptionOverride
    
    def bucket(self):
        return self._bucket

    def matches(self, aDescription):
        return self._condition.satisfies(aDescription)


class ActivityEnrichmentSpecBuilder():
    
    def __init__(self):
        self._definitions = []

    def addDefintionSpecForDescriptionIncludingString(self, bucket, descriptionOverride, aString):
        condition = ActivityDescriptionIncludesStringCondition.forString(aString)
        aDefinition = ActivityEnrichmentSpecDefinition.withBucketDescriptionOverrideAndCondition(bucket, descriptionOverride, condition)
        self.addNewDefinition(aDefinition)
    
    def addDefintionSpecForCodeBasedCondition(self, bucket, descriptionOverride, conditionCode):
        condition = ActivityPluggableCondition.usingCode(conditionCode)
        aDefinition = ActivityEnrichmentSpecDefinition.withBucketDescriptionOverrideAndCondition(bucket, descriptionOverride, condition)
        self.addNewDefinition(aDefinition)

    def addDefintionSpecForDescriptionIncludingAnyOfGivenStrings(self, bucket, descriptionOverride, conditionStrings):
        conditions = [ActivityDescriptionIncludesStringCondition.forString(aString) for aString in conditionStrings ]
        compositeCondition = ActivityAggregationCompositeCondition.withConditions(conditions)
        aDefinition = ActivityEnrichmentSpecDefinition.withBucketDescriptionOverrideAndCondition(bucket, descriptionOverride, compositeCondition)
        self.addNewDefinition(aDefinition)

    def addNewDefinition(self, aDefinition):
        self._definitions.append(aDefinition)

    def fullSpec(self):
        return ActivityEnrichmentSpec.withDefinitions(self._definitions) 