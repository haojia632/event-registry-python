﻿import unittest, sys
from eventregistry import *
from DataValidator import DataValidator

class TestQueryEvent(DataValidator):

    def getValidEvent(self):
        q = QueryEvents(lang = "eng", conceptUri = self.er.getConceptUri("Google"))
        q.setRequestedResult(RequestEventsUriWgtList(count = 1, sortBy="size"))
        res = self.er.execQuery(q)
        return EventRegistry.getUriFromUriWgt(res["uriWgtList"]["results"])[0]


    def testEventArticleFiltering(self):
        q1 = QueryEventArticlesIter("eng-2860795")
        counts1 = q1.count(self.er)
        counts2 = QueryEventArticlesIter("eng-2860795", lang="eng").count(self.er)
        self.assertTrue(counts1 != counts2)
        counts3 = QueryEventArticlesIter("eng-2860795", conceptUri=self.er.getConceptUri("Donald Trump")).count(self.er)
        self.assertTrue(counts1 != counts3)
        counts4 = QueryEventArticlesIter("eng-2860795", keywords = "Trump").count(self.er)
        self.assertTrue(counts1 != counts4)
        counts5 = QueryEventArticlesIter("eng-2860795", sourceUri = self.er.getNewsSourceUri("fox")).count(self.er)
        self.assertTrue(counts1 != counts5)
        counts6 = QueryEventArticlesIter("eng-2860795", lang="eng", conceptUri=self.er.getConceptUri("Donald Trump")).count(self.er)
        self.assertTrue(counts1 != counts6)

        arts1 = [art for art in q1.execQuery(self.er)]
        self.assertTrue(counts1 == len(arts1))

        q = QueryEvent("eng-2860795")
        q.setRequestedResult(RequestEventArticles(lang="eng", conceptUri=self.er.getConceptUri("Donald Trump")))
        res = self.er.execQuery(q)
        self.assertTrue(counts6 == res["eng-2860795"]["articles"]["totalResults"])



    def testArticleSorting(self):
        q = QueryEventArticlesIter(self.getValidEvent())

        # try ascending order
        wgt = None
        for art in q.execQuery(self.er, sortBy="date", sortByAsc=True):
            if wgt == None:
                wgt = art["wgt"]
            self.assertTrue(art["wgt"] >= wgt)
            wgt = art["wgt"]

        # try descending order
        wgt = None
        for art in q.execQuery(self.er, sortBy="date", sortByAsc=False):
            if wgt == None:
                wgt = art["wgt"]
            self.assertTrue(art["wgt"] <= wgt)
            wgt = art["wgt"]


    def testArticleList(self):
        q = QueryEvent(self.getValidEvent())
        q.setRequestedResult(RequestEventArticles(returnInfo = self.returnInfo))
        res = self.er.execQuery(q)

        for event in list(res.values()):
            if "newEventUri" in event:
                continue
            for article in event.get("articles").get("results"):
                self.ensureValidArticle(article, "testArticleList")


    def testArticleCount(self):
        q = QueryEvent(self.getValidEvent())
        q.setRequestedResult(RequestEventArticleUriWgts())
        res = self.er.execQuery(q)

        for (uri, event) in res.items():
            if "newEventUri" in event:
                continue
            iter = QueryEventArticlesIter(uri)
            count = iter.count(self.er)
            uriList = event.get("uriWgtList").get("results")
            if count != len(uriList):
                self.fail("Event did not have expected uri wgt list: expected %d, got %d" % (count, len(uriList)))


    def testArticleUris(self):
        q = QueryEvent(self.getValidEvent())
        q.setRequestedResult(RequestEventArticleUriWgts())
        res = self.er.execQuery(q)

        for event in list(res.values()):
            if "newEventUri" in event:
                continue
            self.assertTrue("uriWgtList" in event, "Expected to see 'uriWgtList'")


    def testKeywords(self):
        q = QueryEvent(self.getValidEvent())
        q.setRequestedResult(RequestEventKeywordAggr())
        res = self.er.execQuery(q)

        for event in list(res.values()):
            if "newEventUri" in event:
                continue
            self.assertIsNotNone(event.get("keywordAggr"), "Expected to see 'keywordAggr'")
            if isinstance(event.get("keywordAggr"), dict) and "error" in event.get("keywordAggr"):
                print("Got error: " + event.get("keywordAggr").get("error"))
                continue
            for kw in event.get("keywordAggr").get("results"):
                self.assertIsNotNone(kw.get("keyword"), "Keyword expected")
                self.assertIsNotNone(kw.get("weight"), "Weight expected")

    def testSourceAggr(self):
        q = QueryEvent(self.getValidEvent())
        q.setRequestedResult(RequestEventSourceAggr())
        res = self.er.execQuery(q)

        for event in list(res.values()):
            if "newEventUri" in event:
                continue
            self.assertIsNotNone(event.get("sourceExAggr"), "Expected to see 'sourceExAggr'")


    def testArticleTrend(self):
        q = QueryEvent(self.getValidEvent())
        q.setRequestedResult(RequestEventArticleTrend())
        res = self.er.execQuery(q)

        for event in list(res.values()):
            if "newEventUri" in event:
                continue
            self.assertIsNotNone(event.get("articleTrend"), "Expected to see 'articleTrend'")


    def testSimilarEvents(self):
        q = QueryEvent(self.getValidEvent())
        q.setRequestedResult(RequestEventSimilarEvents(
            [{ "uri": "http://en.wikipedia.org/wiki/Barack_Obama", "wgt": 100 }, { "uri": "http://en.wikipedia.org/wiki/Donald_Trump", "wgt": 80 }],
            addArticleTrendInfo = True, returnInfo = self.returnInfo))
        res = self.er.execQuery(q)

        for event in list(res.values()):
            if "newEventUri" in event:
                continue
            self.assertIsNotNone(event.get("similarEvents"), "Expected to see 'similarEvents'")
            for simEvent in event.get("similarEvents").get("results"):
                self.ensureValidEvent(simEvent, "testSimilarEvents")
            self.assertIsNotNone(event.get("similarEvents").get("trends"), "Expected to see a 'trends' property")


    def testSimilarStories(self):
        q = QueryEvent(self.getValidEvent())
        q.setRequestedResult(RequestEventSimilarStories(
            [{ "uri": "http://en.wikipedia.org/wiki/Barack_Obama", "wgt": 100 }, { "uri": "http://en.wikipedia.org/wiki/Donald_Trump", "wgt": 80 }],
            returnInfo = self.returnInfo))
        res = self.er.execQuery(q)

        for event in list(res.values()):
            if "newEventUri" in event:
                continue
            self.assertIsNotNone(event.get("similarStories"), "Expected to see 'similarStories'")
            for simStory in event.get("similarStories").get("results"):
                self.ensureValidStory(simStory, "testSimilarStories")


    def testEventArticlesIterator(self):
        # check that the iterator really downloads all articles in the event
        iter = QueryEventArticlesIter("eng-2866653")
        articleCount = iter.count(self.er)
        articles = [art for art in iter.execQuery(self.er)]
        if articleCount != len(articles):
            self.fail("Event article iterator did not generate the full list of event articles")



if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestQueryEvent)
    unittest.TextTestRunner(verbosity=3).run(suite)
