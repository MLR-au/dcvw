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
    xmlns:n="urn:isbn:1-931666-33-4"
    extension-element-prefixes="str"
    exclude-result-prefixes="n str"
    version="1.0">

    <!-- <xsl:import href="../lib/common.xsl" /> -->

    <xsl:output method="text" indent="yes" encoding="UTF-8" omit-xml-declaration="yes" />
    <xsl:template match="/">
        <add>
            <doc>
                <field name="name"><xsl:value-of select="/n:eac-cpf/n:cpfDescription/n:identity/n:nameEntry/n:part" /></field>
                <field name="family_name"><xsl:value-of select="/n:eac-cpf/n:cpfDescription/n:identity/n:nameEntry/n:part[@localType='family_name']" /></field>
                <field name="given_name"><xsl:value-of select="/n:eac-cpf/n:cpfDescription/n:identity/n:nameEntry/n:part[@localType='given_name']" /></field>
                <field name="entity_type"><xsl:value-of select="/n:eac-cpf/n:cpfDescription/n:identity/n:entityType" /></field>
                <field name="date_from"><xsl:value-of select="/n:eac-cpf/n:cpfDescription/n:description/n:existDates/n:dateSet/n:dateRange/n:fromDate/@standardDate" /></field>
                <field name="date_to"><xsl:value-of select="/n:eac-cpf/n:cpfDescription/n:description/n:existDates/n:dateSet/n:dateRange/n:toDate/@standardDate" /></field>
            </doc>
        </add>
    </xsl:template>
</xsl:stylesheet>