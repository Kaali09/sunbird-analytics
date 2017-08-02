package org.ekstep.analytics.metrics.job

import org.ekstep.analytics.framework.util.CommonUtil
import org.ekstep.analytics.framework.util.JSONUtils
import org.ekstep.analytics.util.SessionBatchModel
import org.apache.spark.rdd.RDD
import org.apache.spark.SparkContext
import org.ekstep.analytics.framework.DerivedEvent
import org.ekstep.analytics.model.SparkSpec
import org.joda.time.DateTime
import org.ekstep.analytics.updater.UpdateItemSummaryDB
import com.datastax.spark.connector.cql.CassandraConnector

class TestItemUsageMetricCreationModel extends SparkSpec(null) {
  
    "ItemUsageMetricCreationModel" should "execute ItemUsageMetricCreationModel successfully" in {

        CassandraConnector(sc.getConf).withSessionDo { session =>
            session.execute("TRUNCATE content_db.item_usage_summary_fact");
        }
        
        val start_date = DateTime.now().toString(CommonUtil.dateFormat)
        val rdd = loadFile[DerivedEvent]("src/test/resources/item-summary-updater/ius_2.log");
        UpdateItemSummaryDB.execute(rdd, None);
        
        val data = sc.parallelize(List(""))
        val rdd2 = ItemUsageMetricCreationModel.execute(data, Option(Map("start_date" -> start_date.asInstanceOf[AnyRef], "end_date" -> start_date.asInstanceOf[AnyRef])));
        
        rdd2.count() should be(14)
    }
}