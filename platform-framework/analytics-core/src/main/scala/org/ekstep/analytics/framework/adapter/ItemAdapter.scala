package org.ekstep.analytics.framework.adapter

import org.ekstep.analytics.framework.Item
import org.ekstep.analytics.framework.ItemSet
import org.ekstep.analytics.framework.Questionnaire
import org.ekstep.analytics.framework.util.RestUtil
import org.ekstep.analytics.framework.Response
import org.ekstep.analytics.framework.util.Constants
import org.ekstep.analytics.framework.exception.DataAdapterException
import org.ekstep.analytics.framework.exception.DataAdapterException
import scala.collection.mutable.ListBuffer
import org.ekstep.analytics.framework.Questionnaire
import org.ekstep.analytics.framework.ItemSet
import org.ekstep.analytics.framework.Item
import org.ekstep.analytics.framework.Search
import org.ekstep.analytics.framework.Request
import org.ekstep.analytics.framework.SearchFilter
import org.ekstep.analytics.framework.Metadata
import org.ekstep.analytics.framework.util.JSONUtils
import scala.collection.immutable.List
import scala.collection.immutable.Map
import scala.collection.JavaConversions._
import org.ekstep.analytics.framework.util.CommonUtil
import org.ekstep.analytics.framework.ItemConcept

/**
 * @author Santhosh
 */
object ItemAdapter {

    val relations = Array("concepts", "questionnaires", "item_sets", "items");

    @throws(classOf[DataAdapterException])
    def getItem(itemId: String, subject: String): Item = {
        val ir = RestUtil.get[Response](Constants.getItemAPIUrl(itemId, subject));
        if (!ir.responseCode.equals("OK")) {
            throw new DataAdapterException(ir.responseCode);
        }
        val item = ir.result.assessment_item.get;
        getItemWrapper(item);
    }

    def getItemConceptMaxScore(contentId: String, itemId: String, apiVersion: String = "v1"): ItemConcept = {

        var resMap = Map[String, AnyRef]();
        val cr = RestUtil.get[Response](Constants.getItemConcept(apiVersion, contentId, itemId));
        ItemConcept(cr.result.concepts.getOrElse(null), cr.result.maxScore.getOrElse(1));
    }

    private def getItemWrapper(item: Map[String, AnyRef]): Item = {
        val mc = item.getOrElse("concepts", List[Map[String, String]]()).asInstanceOf[List[AnyRef]].map(f => f.asInstanceOf[Map[String, String]].get("identifier").get).toArray;
        Item(item.get("identifier").get.asInstanceOf[String], item.filterNot(p => relations.contains(p._1)), CommonUtil.getTags(item), Option(mc), None);
    }

    @throws(classOf[DataAdapterException])
    def getItems(contentId: String): Array[Item] = {
        val cr = RestUtil.get[Response](Constants.getContentAPIUrl(contentId));
        if (!cr.responseCode.equals("OK")) {
            throw new DataAdapterException(cr.responseCode);
        }
        val content = cr.result.content.get;
        val questionnaires = content.getOrElse("questionnaires", null);
        val subject = content.get("subject").get.asInstanceOf[String];
        if (questionnaires != null) {
            questionnaires.asInstanceOf[List[AnyRef]].map(f => {
                val qmap = f.asInstanceOf[Map[String, String]];
                val qr = RestUtil.get[Response](Constants.getQuestionnaireAPIUrl(qmap.get("identifier").get, subject));
                val questionnaire = qr.result.questionnaire.get;
                val itemSet = questionnaire.getOrElse("items", Map[String, AnyRef]()).asInstanceOf[Map[String, List[String]]];
                itemSet.map(f => {
                    f._2
                }).reduce((a, b) => a ++ b);
            }).reduce((a, b) => a ++ b).map { x => getItem(x, subject) }.toArray;
        } else {
            null;
        }
    }

    @throws(classOf[DataAdapterException])
    def searchItems(itemIds: Array[String], subject: String): Array[Item] = {
        val search = Search(Request(Metadata(Array(SearchFilter("identifier", "in", Option(itemIds)))), itemIds.length));
        val sr = RestUtil.post[Response](Constants.getSearchItemAPIUrl(subject), JSONUtils.serialize(search));
        val items = sr.result.assessment_items.getOrElse(null);
        if (null != items && items.nonEmpty) {
            items.map(f => getItemWrapper(f));
        } else {
            null;
        }
    }

    @throws(classOf[DataAdapterException])
    def getItemSet(itemSetId: String, subject: String): ItemSet = {
        val isr = RestUtil.get[Response](Constants.getItemSetAPIUrl(itemSetId, subject));
        if (!isr.responseCode.equals("OK")) {
            throw new DataAdapterException(isr.responseCode);
        }
        val itemSet = isr.result.assessment_item_set.get;
        val metadata = itemSet.filterNot(p => relations.contains(p._1));
        val items = itemSet.getOrElse("items", List[String]()).asInstanceOf[List[String]].map(f => {
            getItem(f, subject);
        }).toArray;
        ItemSet(itemSetId, metadata, items, CommonUtil.getTags(itemSet), items.length);
    }

    @throws(classOf[DataAdapterException])
    def getItemSets(contentId: String): Array[ItemSet] = {
        val cr = RestUtil.get[Response](Constants.getContentAPIUrl(contentId));
        if (!cr.responseCode.equals("OK")) {
            throw new DataAdapterException(cr.responseCode);
        }
        val content = cr.result.content.get;
        val questionnaires = content.getOrElse("questionnaires", null);
        val subject = content.get("subject").get.asInstanceOf[String];
        if (questionnaires != null) {
            questionnaires.asInstanceOf[List[AnyRef]].map(f => {
                val qmap = f.asInstanceOf[Map[String, String]];
                val qr = RestUtil.get[Response](Constants.getQuestionnaireAPIUrl(qmap.get("identifier").get, subject));
                val questionnaire = qr.result.questionnaire.get;
                questionnaire.getOrElse("item_sets", List[Map[String, AnyRef]]()).asInstanceOf[List[AnyRef]].map(f => {
                    val map = f.asInstanceOf[Map[String, AnyRef]];
                    map.get("id").get.asInstanceOf[String];
                })
            }).reduce((a, b) => a ++ b).map { x => getItemSet(x, subject) }.toArray;
        } else {
            null;
        }
    }

    @throws(classOf[DataAdapterException])
    def getQuestionnaire(questionnaireId: String, subject: String): Questionnaire = {

        val qr = RestUtil.get[Response](Constants.getQuestionnaireAPIUrl(questionnaireId, subject));
        if (!qr.responseCode.equals("OK")) {
            throw new DataAdapterException(qr.responseCode);
        }
        val questionnaire = qr.result.questionnaire.get;
        val metadata = questionnaire.filterNot(p => relations.contains(p._1));
        val itemSets = questionnaire.getOrElse("item_sets", List[Map[String, AnyRef]]()).asInstanceOf[List[AnyRef]].map(f => {
            val map = f.asInstanceOf[Map[String, AnyRef]];
            getItemSet(map.get("id").get.asInstanceOf[String], subject);
        }).toArray;
        val items = itemSets.map { x => x.items }.reduce((a, b) => a ++ b);
        Questionnaire(questionnaireId, metadata, itemSets, items, CommonUtil.getTags(questionnaire));
    }

    @throws(classOf[DataAdapterException])
    def getQuestionnaires(contentId: String): Array[Questionnaire] = {
        val cr = RestUtil.get[Response](Constants.getContentAPIUrl(contentId));
        if (!cr.responseCode.equals("OK")) {
            throw new DataAdapterException(cr.responseCode);
        }
        val content = cr.result.content.get;
        val questionnaires = content.getOrElse("questionnaires", null);
        val subject = content.get("subject").get.asInstanceOf[String];
        if (questionnaires != null) {
            questionnaires.asInstanceOf[List[AnyRef]].map(f => {
                val map = f.asInstanceOf[Map[String, String]];
                getQuestionnaire(map.get("identifier").get, subject);
            }).toArray;
        } else {
            null;
        }
    }

}