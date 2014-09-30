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
    version="1.0">

    <!-- <xsl:import href="../lib/common.xsl" /> -->

    <xsl:output method="text" indent="yes" encoding="UTF-8" omit-xml-declaration="yes" />
    <xsl:template match="/">
        <add>
            <doc>
                <field name="title"><xsl:value-of select="/n:mods/n:titleInfo/n:title" /></field>
                <field name="volume"><xsl:value-of select="/n:mods/n:titleInfo/n:partNumber" /></field>
                <field name="part"><xsl:value-of select="/n:mods/n:titleInfo/n:partName" /></field>
                <field name="editor"><xsl:value-of select="/n:mods/n:name/n:displayForm" /></field>
            </doc>
        </add>
    </xsl:template>
</xsl:stylesheet>