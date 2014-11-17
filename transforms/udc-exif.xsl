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
    version="1.0">

    <!-- <xsl:import href="../lib/common.xsl" /> -->

    <xsl:output method="text" indent="yes" encoding="UTF-8" omit-xml-declaration="yes" />
    <xsl:template match="/">
        <add>
            <doc>
                <xsl:for-each select="/IIIRECORD/VARFLD/HEADER/TAG">
                    <xsl:variable name="entry" select="."></xsl:variable>
                    <xsl:choose>
                        <xsl:when test="$entry = 'AUTHOR'">
                            <field name="author"><xsl:value-of select="normalize-space(../../MARCSUBFLD/SUBFIELDDATA)" /></field>
                        </xsl:when>
                        <xsl:when test="$entry = 'TITLE'">
                            <field name="title"><xsl:value-of select="normalize-space(../../MARCSUBFLD/SUBFIELDDATA)" /></field>
                        </xsl:when>
                        <xsl:when test="$entry = 'IMPRINT'">
                            <field name="imprint">
                                <xsl:value-of select="normalize-space(../../MARCSUBFLD[1]/SUBFIELDDATA)" />
                                <xsl:text> </xsl:text>
                                <xsl:value-of select="normalize-space(../../MARCSUBFLD[2]/SUBFIELDDATA)" />
                                <xsl:text> </xsl:text>
                                <xsl:value-of select="normalize-space(../../MARCSUBFLD[3]/SUBFIELDDATA)" />
                            </field>
                        </xsl:when>
                        <xsl:when test="$entry = 'SUBJECT'">
                            <field name="subject"><xsl:value-of select="normalize-space(../../MARCSUBFLD/SUBFIELDDATA)" /></field>
                        </xsl:when>
                    </xsl:choose>
                </xsl:for-each>
            </doc>
        </add>
    </xsl:template>
</xsl:stylesheet>