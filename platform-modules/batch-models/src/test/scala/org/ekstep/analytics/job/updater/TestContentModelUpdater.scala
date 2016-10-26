package org.ekstep.analytics.job.updater

import org.ekstep.analytics.model.SparkSpec
import org.ekstep.analytics.framework.JobConfig
import org.ekstep.analytics.framework.Fetcher
import org.ekstep.analytics.framework.Query
import org.ekstep.analytics.framework.Dispatcher
import org.ekstep.analytics.framework.util.JSONUtils

class TestContentModelUpdater extends SparkSpec(null) {
    
    "ContentModelUpdater" should "execute the job and shouldn't throw any exception" in {
        val config = JobConfig(Fetcher("local", None, Option(Array(Query(None, None, None, None, None, None, None, None, None, Option("src/test/resources/content-popularity/test-data.json"))))), None, None, "org.ekstep.analytics.updater.UpdateContentPopularity", None, Option(Array(Dispatcher("console", Map("printEvent" -> false.asInstanceOf[AnyRef])))), Option(10), Option("Content Popularity Updater Test"), Option(false))
        ContentModelUpdater.main(JSONUtils.serialize(config))(Option(sc));
    }

}