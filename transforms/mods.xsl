<?xml version="1.0" encoding="UTF-8"?>
<!-- 
    EAC-CPF to Apache Solr Input Document Format Transform
    Copyright 2013 eScholarship Research Centre, University of Melbourne
    
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
    
        http://www.apache.org/licenses/LICENSE-2.0
    
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
-->
<xsl:stylesheet 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
    xmlns:str="http://exslt.org/strings"
    xmlns:n="http://www.loc.gov/mods/v3"
    extension-element-prefixes="str"
    exclude-result-prefixes="n str"
    version="1.0">

    <!-- <xsl:import href="../lib/common.xsl" /> -->

    <xsl:output method="text" indent="yes" encoding="UTF-8" omit-xml-declaration="yes" />
    <xsl:template match="/">
        <add>
            <doc>
                <field name="title"><xsl:value-of select="/n:mods/n:titleInfo[1]/n:title" /></field>
                <xsl:apply-templates select="/n:mods/n:name/n:displayForm"></xsl:apply-templates>
                <field name="document_type"><xsl:value-of select="/n:mods/n:genre" /></field>
                <field name="date_created"><xsl:value-of select="/n:mods/n:originInfo/n:dateCreated" /></field>
                <field name="abstract"><xsl:value-of select="/n:mods/n:abstract" /></field>
                <field name="journal"><xsl:value-of select="/n:mods/n:relatedItem/n:titleInfo/n:title" /></field>
                <field name="volume"><xsl:value-of select="/n:mods/n:relatedItem/n:part/n:detail[@type='volume']/n:number" /></field>
                <field name="pages"><xsl:value-of select="/n:mods/n:relatedItem/n:part/n:extent[@unit='pages']/n:list" /></field>
                <field name="phys_description"><xsl:value-of select="/n:mods/n:physicalDescription/n:note" /></field>
                <field name="publisher"><xsl:value-of select="/n:mods/n:originInfo/n:publisher" /></field>
                <field name="place"><xsl:value-of select="/n:mods/n:originInfo/n:place/n:placeTerm" /></field>
                <field name="record_type">Bibliographic Records (MODS XML)</field>
                <xsl:apply-templates select="/n:mods/n:subject/n:topic"></xsl:apply-templates>
                <xsl:apply-templates select="/n:mods/n:subject/n:temporal"></xsl:apply-templates>
                <xsl:apply-templates select="/n:mods/n:subject/n:geographic"></xsl:apply-templates>
                <xsl:apply-templates select="/n:mods/n:subject/n:name[@type='corporate']/n:namePart"></xsl:apply-templates>
            </doc>
        </add>
    </xsl:template>
    <xsl:template match="/n:mods/n:name/n:displayForm">
        <xsl:variable name="role" select="../n:role/n:roleTerm" />
        <xsl:choose>
            <xsl:when test="$role = 'author'">
                <field name="author"><xsl:value-of select="." /></field>
            </xsl:when>
            <xsl:when test="$role = 'editor'">
                <field name="editor"><xsl:value-of select="." /></field>
            </xsl:when>
            <xsl:when test="$role = 'contributor'">
                <field name="contributor"><xsl:value-of select="." /></field>
            </xsl:when>
        </xsl:choose>
        <field name="name_role"><xsl:value-of select="." /></field>
    </xsl:template>
    <xsl:template match="/n:mods/n:subject/n:topic">
        <field name="subject_topic"><xsl:value-of select="." /></field>
    </xsl:template>
    <xsl:template match="/n:mods/n:subject/n:temporal">
        <field name="subject_temporal"><xsl:value-of select="." /></field>
    </xsl:template>
    <xsl:template match="/n:mods/n:subject/n:geographic">
        <field name="subject_geographic"><xsl:value-of select="." /></field>
    </xsl:template>
    <xsl:template match="/n:mods/n:subject/n:name[@type='corporate']/n:namePart">
        <field name="subject_corporate"><xsl:value-of select="." /></field>
    </xsl:template>
</xsl:stylesheet>