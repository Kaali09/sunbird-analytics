package org.ekstep.analytics.job

import org.ekstep.analytics.model.SparkSpec
import org.ekstep.analytics.framework.JobConfig
import org.ekstep.analytics.framework.Fetcher
import org.ekstep.analytics.framework.Query
import org.ekstep.analytics.framework.Dispatcher
import org.ekstep.analytics.framework.util.JSONUtils
import org.ekstep.analytics.framework.Filter

class TestDeviceContentUsageSummarizer extends SparkSpec(null) {

    "DeviceContentUsageSummarizer" should "execute the job and shouldn't throw any exception" in {
        val config = JobConfig(Fetcher("local", None, Option(Array(Query(None, None, None, None, None, None, None, None, None, Option("src/test/resources/device-content-usage-summary/test_data1.log"))))), None, None, "org.ekstep.analytics.model.DeviceContentUsageSummary", None, Option(Array(Dispatcher("console", Map("printEvent" -> false.asInstanceOf[AnyRef])))), Option(10), Option("TestDeviceContentUsageSummarizer"), Option(false))
        DeviceContentUsageSummarizer.main(JSONUtils.serialize(config))(Option(sc));
    }
}